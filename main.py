import glob
import os
import errno
from time import sleep

from kubernetes import client, config
import logging
import yaml
import time
import sys
import datetime
import requests

from kubernetes.client import ApiException

from helpers import merge_dicts


### logging construction ###############
clogger = logging.getLogger(__name__)
c_handler = logging.StreamHandler(sys.stdout)
format = logging.Formatter("%(asctime)s.%(msecs)03d %(message)s", datefmt="%H:%M:%S")
c_handler.setFormatter(format)
clogger.addHandler(c_handler)
clogger.setLevel(logging.INFO)

# Load kube config
config.load_kube_config()

def wait_for_deployment_complete(v1_apps, deployment_name, ns, timeout=360):
    clogger.info(f'Update deployment:{deployment_name}')
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(2)
        response = v1_apps.read_namespaced_deployment_status(deployment_name, ns)
        s = response.status
        if (s.updated_replicas == response.spec.replicas and
                s.replicas == response.spec.replicas and
                s.available_replicas == response.spec.replicas and
                s.observed_generation >= response.metadata.generation):
            return True
        else:
            clogger.info(f'[updated_replicas:{s.updated_replicas},replicas:{s.replicas}'
                  ',available_replicas:{s.available_replicas},observed_generation:{s.observed_generation}] waiting...')

    raise RuntimeError(f'Waiting timeout for deployment {deployment_name}')

def configmap_add_data(cm_name, cm_ns, path_new_data):
    """Add some data to configMap

    Args:
        cm_name (str): the name of configMap that needs to be updated
        cm_ns (str): the namespace of configMap that needs to be updated
        path_new_data (str): the path to the data to be added to ConfigMap
    """
    v1 = client.CoreV1Api()

    configmap = v1.read_namespaced_config_map(cm_name, cm_ns)
    configmap_data = yaml.safe_load(configmap.data['config.yaml'])

    with open(path_new_data, 'r') as f:
        new_configmap_data = yaml.safe_load(f)

    merged_cm_data = merge_dicts(configmap_data, new_configmap_data)
    configmap.data['config.yaml'] = yaml.dump(merged_cm_data)
    v1.replace_namespaced_config_map(cm_name, cm_ns, configmap)


def restart_deployments(v1_apps, deployment, ns):
    """Restart deployments and wait for it to be ready

    Args:
        v1_apps (object): k8s api object
        deployment (str): the name of deployment to restart
        ns (str): the namespace of deplyments
    """
    now = datetime.datetime.utcnow()
    now = str(now.isoformat("T") + "Z")
    body = {
        'spec': {
            'template': {
                'metadata': {
                    'annotations': {
                        'kubectl.kubernetes.io/restartedAt': now
                    }
                }
            }
        }
    }
    try:
        v1_apps.patch_namespaced_deployment(deployment, ns, body, pretty='true')
    except ApiException as e:
        print("Exception when calling AppsV1Api->read_namespaced_deployment_status: %s\n" % e)

def send_query_to_loki(endpoint, loki_query):
    """Send log request to loki

    Args:
        endpoint (str)
        loki_query (str): logql query for loki
    """
    #loki_query = ('{log_type="container", app_name=~"logmaker", app_instance=~".*", app_component=~".*", '
    #              'namespace=~"personal-anmakarov", pod=~".*", container=~".*"} |> "<_>' + str(search_int) + '<_>" '
    #              '| json | line_format "{{.message}}"' + "&start=" + str(int(start_time)) + "&end=" +
    #                str(int(end_time)) + "&limit=1000")
    result_query = endpoint + "?query=" + loki_query
    r = requests.get(result_query, headers={"X-Scope-OrgID": "personal-anmakarov|system-logging-new"}, timeout=120)

    return r.status_code


def prepare_test_results(start_time, end_time, stats):
    """Prepare results of test

    Args:
        end_time (int):
        start_time (int):
        stats (dict):
    """
    filename = "./results.txt"
    if not os.path.exists(os.path.dirname(filename)):
        try:
            os.makedirs(os.path.dirname(filename))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

    dashboard_link = (f'https://dev-monitor.sbis.ru/d/PK9eSrJVz/k8s-sistema-sbora-logov-rasshirennyj?orgId=1&from={start_time}&to={end_time}'
                      f'&var-datasource=adm-k8s-dpc24&var-tenant=dpc24&var-environment=adm&var-cluster=feature2'
                      f'-core-dpc&var-Loki_datasource=adm-k8s-dpc24-feature2-core-dpc')

    with open(filename, "a") as myfile:
        myfile.write(stats["name"] + '\n')
        myfile.write(dashboard_link + '\n')
if __name__ == "__main__" :
    clogger.info("Start script")
    endpoint = "http://10.236.204.2:3100/loki/api/v1/query_range"
    times = [
        (1730974531, 1730983246)
    ]
    search_strings = [".*", "234781", "32478"]
    logs_queries = [
        '{{log_type="container", app_name=~"logmaker", app_instance=~".*", app_component=~".*", '
        'namespace=~"personal-anmakarov", pod=~".*", container=~".*"}} | "(?i){search_string}" | json | line_format "{{{{.message}}}}"' +
        "&start={start_time}&end={end_time}&limit=1000",

        '{{log_type="container", app_name=~"logmaker", app_instance=~".*", app_component=~".*", '
        'namespace=~"personal-anmakarov", pod=~".*", container=~".*"}} | json | message=~"{search_string}" | line_format "{{{{.message}}}}"' +
        "&start={start_time}&end={end_time}&limit=1000",
    ]
    count_queries = [
        'sum(count_over_time({{log_type="container", app_name=~"logmaker", app_instance=~".*", app_component=~".*", '
        'namespace=~"personal-anmakarov", pod=~".*", container=~".*"}} | "(?i){search_string}" [{interval_query}ms]' +
        "&start={start_time}&end={end_time}",

        'sum(count_over_time({{log_type="container", app_name=~"logmaker", app_instance=~".*", app_component=~".*", '
        'namespace=~"personal-anmakarov", pod=~".*", container=~".*"}} | json | message=~"{search_string}" [{interval_query}ms]))' +
        "&start={start_time}&end={end_time}",
    ]
    for loki_conf in glob.glob('conf_variants/*.yaml', recursive=True):
        ok_status_counter = 0
        err_status_counter = 0
        v1_apps = client.AppsV1Api()

        configmap_add_data("loki-loki-distributed", "system-logging-new", loki_conf)

        restart_deployments(v1_apps, "loki-loki-distributed-query-scheduler", "system-logging-new")
        restart_deployments(v1_apps, "loki-loki-distributed-querier", "system-logging-new")
        restart_deployments(v1_apps, "loki-loki-distributed-query-frontend", "system-logging-new")

        wait_for_deployment_complete(v1_apps, "loki-loki-distributed-query-scheduler", "system-logging-new")
        wait_for_deployment_complete(v1_apps, "loki-loki-distributed-querier", "system-logging-new")
        wait_for_deployment_complete(v1_apps, "loki-loki-distributed-query-frontend", "system-logging-new")

        time.sleep(15)
        for time_pair in times:
            start_script_time = int(time.time())
            start_time = time_pair[0]
            end_time = time_pair[1]
            interval_time = round((end_time-start_time)/1500, -2)
            for search_string in search_strings:
                for query in logs_queries:
                    status_code = send_query_to_loki(endpoint, query.format(search_string=search_string, start_time = start_time, end_time=end_time))
                    if status_code < 200 or status_code > 240:
                        err_status_counter+=1
                    else:
                        ok_status_counter+=1
                    time.sleep(1)

                for query in count_queries:
                    status_code = send_query_to_loki(endpoint, query.format(search_string=search_string, interval_query=interval_time ,start_time = start_time, end_time=end_time))
                    if status_code < 200 or status_code > 240:
                        err_status_counter+=1
                    else:
                        ok_status_counter+=1
                    time.sleep(1)
                time.sleep(15)
        prepare_test_results(start_script_time, int(time.time()), {"name": loki_conf})
        time.sleep(10)