from kubernetes import client, config
import logging
import yaml

### logging construction ###############
clogger = logging.getLogger(__name__)
c_handler = logging.StreamHandler(sys.stdout)
format = logging.Formatter("%(asctime)s.%(msecs)03d %(message)s", datefmt="%H:%M:%S")
c_handler.setFormatter(format)
clogger.addHandler(c_handler)
clogger.setLevel(logging.INFO)

# Load kube config
config.load_kube_config()

def configmap_add_data(cm_name, cm_ns, path_new_data):
    """Add some data to configMap

    Args:
        cm_name (str): the name of configMap that needs to be updated
        cm_ns (str): the namespace of configMap that needs to be updated
        path_new_data (str): the path to the data to be added to ConfigMap
    """

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