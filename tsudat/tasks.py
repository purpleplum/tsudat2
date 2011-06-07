import os, sys
import logging
import shutil
import simplejson as json
import tempfile
from time import gmtime, strftime, sleep

from django import db
from django.contrib.auth.models import User
from django.conf import settings

from owslib.wcs import WebCoverageService

from tsudat.models import *
from celery.decorators import task
from geonode.maps.models import *
from geonode.maps.utils import *

from osgeo import gdal
from gdalconst import *
import osr

from util.LatLongUTMconversion import LLtoUTM 
from run_tsudat import run_tsudat_nci as run_tsudat

import re

try:
    from notification import models as notification
except ImportError:
    notification = None

logger = logging.getLogger("tsudat2.tsudat.tasks")

# Move somewhere more accessible
_slugify_strip_re = re.compile(r'[^\w\s-]')
_slugify_hyphenate_re = re.compile(r'[-\s]+')
def _slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    
    From Django's "django/template/defaultfilters.py".
    """
    import unicodedata
    if not isinstance(value, unicode):
        value = unicode(value)
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = unicode(_slugify_strip_re.sub('', value).strip().lower())
    return _slugify_hyphenate_re.sub('-', value)

@task
def run_tsudat_simulation(user, scenario_id):
    """
    Generate a working directory for running ANUGA
    Create/Copy all of the files to that directory that are necessary
    for running the simulation. Generate a json run file and call run_tsudat.
    Notes here: https://github.com/AIFDR/tsudat2/wiki/Create-anuga-run-script
    """

    # Get the scenario object from the Database
    scenario = Scenario.objects.get(id=scenario_id)
    
    # the base of the TsuDAT user directory structures from settings.py 
    TsuDATBase = settings.TSUDAT_BASE_DIR
    TsuDATMux = settings.TSUDAT_MUX_DIR

    # create the user working directory
    (work_dir, raw_elevations, boundaries, meshes,
             polygons, gauges) = run_tsudat.make_tsudat_dir(TsuDATBase, user.username, _slugify(scenario.project.name),
                                                            _slugify(scenario.name), scenario.model_setup, scenario.event.tsudat_id)

    project_geom = scenario.project.geom
    project_extent = scenario.project.geom.extent
    centroid = project_geom.centroid

    # This somewhat naively assumes that the whole bounding polygon is in the same zone
    (UTMZone, UTMEasting, UTMNorthing) = LLtoUTM(23, centroid.coords[1], centroid.coords[0])
    if(len(UTMZone) == 3):
        utm_zone = int(UTMZone[0:2])
    else:
        utm_zone = int(UTMZone[0:1])
    if(centroid.coords[1] > 0):
        srid_base = 32600
    else:
        srid_base = 32700
    srid = srid_base + utm_zone

    project_geom.transform(srid) 

    # Polygons
    print polygons
    bounding_polygon_file = open(os.path.join(polygons, 'bounding_polygon.csv'), 'w')
    for coord in project_geom.coords[0]:
        bounding_polygon_file.write('%f,%f\n' % (coord[0], coord[1]))
    bounding_polygon_file.close()
 
    # Internal Polygons 
    internal_polygons = InternalPolygon.objects.filter(project=scenario.project).order_by('value')
    count = 0
    InteriorRegions = []
    for ip in internal_polygons:
        ipfile = open(os.path.join(polygons, 'ip%s.csv' % count), 'w')
        geom = ip.geom
        geom.transform(srid)
        for coord in geom.coords[0]:
            ipfile.write('%f,%f\n' % (coord[0], coord[1]))
        InteriorRegions.append([ip.type, ipfile.name, ip.value])
        ipfile.close()
        geom = ipfile = None
        count += 1

    # Raw Elevation Files
    RawElevationFiles = []

    wcs_url = settings.GEOSERVER_BASE_URL + 'wcs'
    wcs = WebCoverageService(wcs_url, version='1.0.0')
    pds = ProjectDataSet.objects.filter(project=scenario.project).order_by('ranking')
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(srid)
    dst_wkt = srs.ExportToPrettyWkt()
    eResampleAlg = None
    create_options = None
    
    output_format = "AAIGrid"
    driver = gdal.GetDriverByName(output_format)
    
    for ds in pds:
        layer = Layer.objects.get(uuid=ds.dataset.geonode_layer_uuid)
        logger.info(wcs.contents)
        metadata = wcs.contents[layer.typename]
        print metadata.grid
        resx = metadata.grid.offsetvectors[0][0]
        resy = abs(float(metadata.grid.offsetvectors[1][1]))
        formats = metadata.supportedFormats
        print formats
        cvg = wcs.getCoverage(identifier=layer.typename, 
                format='GeoTIFF', 
                crs="EPSG:4326", 
                bbox=(project_extent[0], 
                    project_extent[1], 
                    project_extent[2], 
                    project_extent[3]), 
                resx=resx, 
                resy=resy)
        # Need to make sure the ranking numbers are unique for each project (enforced with DB constraint?)
        tif_file_name = '%s.tif' % ds.ranking
        tif_file_path = os.path.join(raw_elevations, tif_file_name)
        asc_file_name = '%s.asc' % ds.ranking
        asc_file_path = os.path.join(raw_elevations, asc_file_name)
        out = open(tif_file_path, 'wb')
        out.write(cvg.read())
        out.close()
       
        # Warp to UTM
        cmd = "/usr/bin/gdalwarp -t_srs EPSG:%d %s %s.tmp" % (srid, tif_file_path, tif_file_path)
        os.system(cmd)
        # Convert to AAIGrid
        cmd = "/usr/bin/gdal_translate -a_nodata -9999 -of %s %s.tmp %s" % (output_format, tif_file_path, asc_file_path)
        os.system(cmd)
        # Remove Intermediate files
        os.remove(tif_file_path)
        os.remove(tif_file_path + ".tmp")
      
        # Rename the .prj file to .prj.wkt
        shutil.move(asc_file_path.replace('.asc', '.prj'), asc_file_path.replace('.asc', '.prj.wkt'))
         
        # Generate a prj.adf style prj file
        # NOTE: Not sure if this will work in all cases?
        prj_file_name = '%s.prj' % ds.ranking
        prj_file = open(os.path.join(raw_elevations, prj_file_name), 'w')
        prj_file.write('Projection    UTM\n')
        prj_file.write('Zone          %d\n' % utm_zone)
        prj_file.write('Datum         WGS1984\n')
        prj_file.write('Zunits        NO\n')
        prj_file.write('Units         METERS\n')
        prj_file.write('Spheroid      WGS_1984\n')
        prj_file.write('Xshift        500000\n')
        prj_file.write('Yshift        10000000\n')
        prj_file.write('Parameters\n')
        prj_file.close()        

        RawElevationFiles.append(asc_file_path)
         
        '''
        src_ds = gdal.Open( str(tif_file_path), GA_ReadOnly )
        dst_ds_tmp = driver.CreateCopy( str(asc_file_name + '.tmp'), src_ds, 0)
        dst_ds = driver.Create( str(asc_file_path), dst_ds_tmp.RasterXSize, dst_ds_tmp.RasterYSize)
        gdal.ReprojectImage(src_ds, dst_ds, None, dst_wkt)
        dst_ds = None
        dst_ds_tmp = None
        src_ds = None
        '''

    # Landward Boundary
    landward_boundary_file = open(os.path.join(boundaries, 'landward_boundary.csv'), 'w')
    for coord in project_geom.coords[0]:
        pnt_wkt = 'SRID=%s;POINT(%f %f)' % (srid, coord[0], coord[1])
        logger.debug(pnt_wkt)
        land = Land.objects.filter(the_geom__intersects=pnt_wkt)
        if(land.count() > 0):
            landward_boundary_file.write('%f,%f\n' % (coord[0], coord[1]))
    landward_boundary_file.close()

    # Interior Hazard Points File
    interior_hazard_points_file = open(os.path.join(boundaries, 'interior_hazard_points.csv'), 'w')
    hps = HazardPoint.objects.filter(geom__intersects=project_geom).order_by('tsudat_id')
    for hp in hps:
        the_geom = hp.geom
        the_geom.transform(srid)
        interior_hazard_points_file.write('%f,%f\n' % (the_geom.coords[0], the_geom.coords[1]))
    interior_hazard_points_file.close()
    
    # Gauges
    gauge_file = open(os.path.join(gauges, 'gauges.csv'), 'w')
    gauge_file.write('easting,northing,name,elevation\n')
    gauge_points = GaugePoint.objects.filter(project=scenario.project)
    for gauge in gauge_points:
        gauge_geom = gauge.geom
        gauge_geom.transform(srid)
        gauge_file.write('%f,%f,%s,%f\n' % (gauge_geom.coords[0], gauge_geom.coords[1], gauge.name, 0.0))
    gauge_file.close()
   
    # Layers 
    scenario_layers = scenario.output_layers.all()
    layers = []
    for layer in scenario_layers:
        layers.append(layer.name)

    # build the scenario json data file
    date_time = strftime("%Y%m%d%H%M%S", gmtime()) 
    json_file = os.path.join(work_dir, '%s.%s.json' % (_slugify(scenario.name), date_time))
               
    json_dict = {
                    'user': user.username,
                    'project': scenario.project.name,
                    'scenario_name': scenario.name,
                    'setup': scenario.model_setup,
                    'event_number': scenario.event.tsudat_id,
                    'working_directory': TsuDATBase,
                    'mux_directory': TsuDATMux,
                    'initial_tide': scenario.initial_tidal_stage,
                    'start_time': scenario.start_time,
                    'end_time': scenario.end_time,
                    'smoothing': scenario.smoothing_param,
                    'bounding_polygon_file': bounding_polygon_file.name,
                    'elevation_data_list': RawElevationFiles,
                    'mesh_friction': scenario.default_friction_value,
                    'raster_resolution': scenario.raster_resolution,
                    'export_area': "AOI" if scenario.use_aoi == True else "ALL",
                    'gauge_file': gauge_file.name,
                    'bounding_polygon_maxarea': scenario.project.max_area,
                    'interior_regions_list': InteriorRegions,
                    'interior_hazard_points_file': interior_hazard_points_file.name, 
                    'landward_boundary': landward_boundary_file.name,
                    'zone': utm_zone,
                    'layers_file': layers, 
                    'get_results_max': True,
                    'get_timeseries': True 
                }

    with open(json_file, 'w') as fd:
        json.dump(json_dict, fd, indent=2, separators=(',', ':'))

    # now run the simulation
    #run_tsudat.run_tsudat(json_file)

    # TEMPORARY!!

    output_file = open('/var/www/tsudat2/data/batemans_bay_output.json', 'r')
    output_json = json.loads(output_file.read())

    # /TEMPORARY

    # Setup the new layers in the GeoNode

    layers = []

    for result in output_json['results_max']:
        layer_title = "Dummy Title"
        layer_abstract = "This layer shows the maximum *flow depth/flow velocity/wave amplitude* from a 1 in *return_period* tsunami that was generated by a magnitude *mag* earthquake on the *source_zone* subduction zone. The tsunami amplitude at the 100 m water depth contour was *waveheight* and the tide height during the simulation was *tide* m. Elevation data used in this tsunami simulation includes *elevation input 1, elevation input 2....*."

        (head, tail) = os.path.split(result)
        (base, ext) = os.path.splitext(tail)
        tif_file_path = result.replace('.asc', '.tif')

        # Warp to 4326 / Convert to TIF
        cmd = "/usr/bin/gdalwarp -of GTiff -s_srs EPSG:%d -t_srs EPSG:4326 %s %s" % (srid, result, tif_file_path)
        print cmd
        os.system(cmd)
        
        new_layer = save(base, tif_file_path, user, overwrite = False, title=layer_title, abstract=layer_abstract, keywords = []) 
        layers.append(new_layer.typename)
        print "layers=" + str(layers)

    # Create a project Map in the GeoNode
    map_title = "%s Project Map" % (scenario.name)
    map_abstract = "%s Project Map Abstract" % (scenario.name)

    map = Map()
    map.create_from_layer_list(user, layers, map_title, map_abstract)
    
    # Notify the User their job is finished

    return True
