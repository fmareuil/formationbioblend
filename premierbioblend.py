#! /usr/bin/python
"""
Cours G4B 2014:
    @contact: fabien.mareuil@pasteur.fr
    @contact: olivia.doppelt@pasteur.fr
    @contact: alban.lermine@pasteur.fr
Script to use Bioblend and interact with
a galaxy instance.
"""
from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.tools.inputs import inputs, dataset
import argparse
import urlparse
import requests
import shlex
import os
import pprint
import sys
import textwrap


def connectgalaxy(apikey, galaxyurl):
    """
    @param apikey:
    @param galaxyurl:
    returns an object galaxyinstance
    """
    return GalaxyInstance(url=galaxyurl, key=apikey)

def _find_history(gi, namehisto):
    histolist = gi.histories.get_histories(name=namehisto)
    if len(histolist) == 0:
        raise ValueError("Il n'y a pas d'historique qui porte ce nom")
    elif len(histolist) > 1:
        raise ValueError("Il y a plus d'un historique qui porte ce nom")
    return histolist[0]

def liste_historyfiles(apikey, galaxyurl, namehisto):
    """
    lists the files in a history
    """
    gi = connectgalaxy(apikey, galaxyurl)
    filesdico = {}
    histo = _find_history(gi, namehisto)
    idhisto = histo["id"]
    liste_data = gi.histories.show_history(histo["id"], contents=False)["state_ids"]["ok"]
    for iddata in liste_data:
        filesdico[gi.datasets.show_dataset(iddata)['id']] = gi.datasets.show_dataset(iddata)['name']
    for data in filesdico:
        print "FILENAME: {0:80} FILE_ID: {1} HISTORY_ID: {2}".format(filesdico[data], data, idhisto)


def run_tool(api_key, galaxy_url, tool_name, name_hist):
    print "not yes implemented or functional"
    return 0



def run_workflow(api_key, galaxy_url, name_wf, name_hist):#, dataset_id):
    dataset_map = {}
    gi = connectgalaxy(api_key, galaxy_url)
    workflow = _find_workflow(gi, name_wf)
    history = _find_history(gi, name_hist)
    dataset_id = gi.histories.show_matching_datasets(history[u'id'])[0]['id']
    dataset_map[workflow[u'inputs'].keys()[0]] = {'id': dataset_id, 'src': 'hda'}
    return gi.workflows.run_workflow(workflow['id'], history_id=history['id'], dataset_map=dataset_map)


#run_workflow(args.api_key, args.galaxy_url, args.name_workflow, args.hist_name, args.filesid)


def _find_workflow(gi, name):
    workflows = gi.workflows.get_workflows(name=name)
    if len(workflows) > 1:
        raise ValueError("Il y a plusieurs workflows qui portent ce nom")
    elif len(workflows) == 0:
        raise ValueError("Pas de Workflow avec ce nom")
    wf_id = workflows[0][u'id']
    return gi.workflows.show_workflow(wf_id)


def specific_download_dataset(gi, dataset, id, idhisto, key, file_path, use_default_filename=True, verify=True):
    download_url = 'api/histories/' + idhisto+ '/contents/' + id + '/display?to_ext=' + dataset['file_ext'] +'&hda_ldda=' + dataset['hda_ldda'] + '&key=' + key
    url = urlparse.urljoin(gi.base_url, download_url)

    r = requests.get(url, verify=verify)
    if file_path is None:
            return r.content
    else:
        if use_default_filename:
            try:
                # First try to get the filename from the response headers
                # We expect tokens 'filename' '=' to be followed by the
                # quoted filename
                tokens = [x for x in shlex.shlex(r.headers['content-type'], posix=True)]
                header_filepath = tokens[tokens.index('filename') + 2]
                filename = os.path.basename(header_filepath)
            except (ValueError, IndexError):
                # If the filename was not in the header, build a useable
                # filename ourselves.
                filename = dataset['name'] + '.' + dataset['file_ext']
            file_local_path = os.path.join(file_path, filename)
        else:
            file_local_path = file_path
        with open(file_local_path, 'wb') as fp:
            fp.write(r.content)


def downloadfile(key, url, datas_ids, namehisto, path):
    gi = connectgalaxy(key, url)
    history = _find_history(gi, namehisto)
    for data_id in datas_ids:
        dataset = gi.datasets.show_dataset(data_id)
        if not dataset['state'] == 'ok':
            print >> sys.stderr, "WARNING : Dataset not ready. Dataset id: %s, current state: %s" % (data_id, dataset['state'])
        else:
            gi.histories.download_dataset(history['id'], data_id, file_path=path)
    #specific_download_dataset(gi, dataset, id, idhisto, key, file_path=path, verify=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("-k", "--api_key", action="store", help="api key of galaxy", required=True)
    parser.add_argument("-u", "--galaxy_url", action="store", help="url of galaxy", required=True)
    parser.add_argument('action', choices=['my_histories','list_history','run_workflow','download_files'],
                         help=textwrap.dedent('''\
                         my_histories: lists yours histories,
                         history_list: lists files of a history, need -n option,
                         run_workflow: runs a workflow, need -w, -n options,
                         run_tool: runs a tool, need -t, -n options,
                         download_files: downloads files, need -n, -f, -p options
                                   '''))
    parser.add_argument("-w", "--name_workflow", action="store", help="name of your workflow")
    parser.add_argument("-n", "--hist_name", action="store", help="name of galaxy history")
    parser.add_argument("-t", "--tool_name", action="store", help="name of galaxy tool")
    parser.add_argument("-f", "--filesid", nargs="+", help="file id to download")
    parser.add_argument("-p", "--path", action="store", help="output path to download")
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')

    args = parser.parse_args()
    if args.action == 'my_histories':
        gi = connectgalaxy(args.api_key, args.galaxy_url)
        pprint.pprint(gi.histories.get_histories())
        #liste_historyfiles(args.galaxy_url, args.api_key)
    elif args.action == 'list_history':
        if args.hist_name:
            liste_historyfiles(args.api_key, args.galaxy_url, args.hist_name)
        else:
            print >> sys.stderr, "the -hi option need a history name, -n option"
    elif args.action == 'run_tool':
        if args.tool_name and args.hist_name:
            run_tool(args.api_key, args.galaxy_url, args.tool, args.hist_name)
        else:
            print >> sys.stderr, "the -t option need a tool name and a history name, -w and -n options"
    elif args.action == 'run_workflow':
        if  args.name_workflow and args.hist_name:
            run_workflow(args.api_key, args.galaxy_url, args.name_workflow, args.hist_name)#, args.filesid)
        else:
            print >> sys.stderr, "the -r option need a workflow name and a history name, -w and -n options"
    elif args.action == 'download_files':
        if args.filesid and args.hist_name and args.path:
            downloadfile(args.api_key, args.galaxy_url, args.filesid, args.hist_name, args.path)
        else:
            print >> sys.stderr, "the -d option need a history name, a liste of dataset_id separate by space and a path, -n, -f and -p options"

