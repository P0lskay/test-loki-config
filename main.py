from kubernetes import client, config
import logging
import yaml
import time

### logging construction ###############
clogger = logging.getLogger(__name__)
c_handler = logging.StreamHandler(sys.stdout)
format = logging.Formatter("%(asctime)s.%(msecs)03d %(message)s", datefmt="%H:%M:%S")
c_handler.setFormatter(format)
clogger.addHandler(c_handler)
clogger.setLevel(logging.INFO)

# Load kube config
config.load_kube_config()


def wait_for_deployment_complete(deployment_name, ns, timeout=360):
    clogger.info(f'Update deployment:{deployment_name}')
    v1apps = client.AppsV1Api()
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(2)
        response = v1apps.read_namespaced_deployment_status(deployment_name, ns)
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

    with open(path_new_data, 'r') as f:
        new_data = yaml.safe_load(f)

    configmap.data.update(new_data)

    v1.replace_namespaced_config_map(cm_name, cm_ns, configmap)


def restart_deployments(deployments_lst, ns):
    """Restart deployments and wait for it to be ready

    Args:
        deployments_lst (list): list with the names of deployments to restart
        ns (_type_): the namespace of deplyments
    """

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