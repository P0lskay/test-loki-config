from kubernetes import client, config
import logging
import yaml
import time
import sys
import datetime

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
        deployment (string): the name of deployment to restart
        ns (string): the namespace of deplyments
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

def send_logs_query_to_loki(query):
    """Send log request to loki

    Args:
        query (string): logql query for loki
    """

def send_count_of_logs_query_to_loki(query):
    """Send request for log counting to loki

    Args:
        query (string): logql query for loki
    """

def prepare_test_results():
    """Prepare results of test
    """

if __name__ == "__main__" :
    clogger.info("Start script")
    v1_apps = client.AppsV1Api()
    #restart_deployments(v1_apps, "loki-loki-distributed-querier", "system-logging-new")
    #wait_for_deployment_complete(v1_apps, "loki-loki-distributed-querier", "system-logging-new")