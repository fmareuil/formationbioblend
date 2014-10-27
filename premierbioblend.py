"""
Cours G4B 2014:
    @contact: fabien.mareuil@pasteur.fr
    @contact: olivia.doppelt@pasteur.fr
    @contact: alban.lermine@pasteur.fr
Script to use Bioblend and interract with
a galaxy instance.
"""
from bioblend.galaxy import GalaxyInstance
import argparse
import urlparse
import requests
import shlex
import os

def connectgalaxy(apikey, galaxyurl):
    """
    @param apikey:
    @param galaxyurl:
    returns an object galaxyinstance
    """
    return GalaxyInstance(url=galaxyurl, key=apikey)

def liste_historyfiles(key, galaxyurl, namehisto):
    """
    lists the files in a history
    """
    gi = connectgalaxy(key, url)
    filesdico = {}
    histolist = gi.histories.get_histories(name="namehisto")
    if len(histolist) == 0:
        raise ValueError("Il n'y a pas d'historique qui porte ce nom")
    elif len(histolist) > 1:
        print "Il y a plus d'un historique qui porte ce nom"
    for histo in histolist:
        if histo["name"] == namehisto:
            idhisto = histo["id"]
            liste_data = gi.histories.show_history(histo["id"],contents=False)["state_ids"]["ok"]
    for iddata in liste_data:
        filesdico[gi.datasets.show_dataset(iddata)['id']] = gi.datasets.show_dataset(iddata)['name']
    return filesdico, idhisto

def run_workflow(key, url, name):
    
    gi = connectgalaxy(key, url)
    workflow = gi.workflows.get_workflows(name=name)
    if len(workflow) > 1:
        raise ValueError("Il y a plusieurs workflows qui portent ce nom")
    elif len(workflow) == 0:
        raise ValueError("Pas de Workflow avec ce nom") 

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
                # We expect tokens 'filename' '=' to be followed by the quoted filename
                tokens = [x for x in shlex.shlex(r.headers['content-type'], posix=True)]
                header_filepath = tokens[tokens.index('filename') + 2]
                filename = os.path.basename(header_filepath)
            except (ValueError, IndexError):
                # If the filename was not in the header, build a useable filename ourselves.
                filename = dataset['name'] + '.' + dataset['file_ext']
            file_local_path = os.path.join(file_path, filename)
        else:
            file_local_path = file_path
        with open(file_local_path, 'wb') as fp:
            fp.write(r.content)

def downloadfile(key, url, id, idhisto, path):
    gi = connectgalaxy(key, url)
    dataset = gi.datasets.show_dataset(id)
    if not dataset['state'] == 'ok':
            raise DatasetStateException("Dataset not ready. Dataset id: %s, current state: %s" % (id, dataset['state']))
    #gi.datasets.download_dataset(id, file_path=path, verify=True)
    specific_download_dataset(gi, dataset, id, idhisto, key, file_path=path, verify=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-k", "--key", action="store", help="api key of galaxy")
    parser.add_argument("-u", "--url", action="store", help="url of galaxy")
    parser.add_argument("-m", "--my_histories", help="list yours histories")
    parser.add_argument("-hi", "--history_list", help="list files of a history")
    parser.add_argument("-n", "--name", action="store", help="name of galaxy history")
    parser.add_argument("-w", "--name_workflow", action="store", help="id of your workflow")
    parser.add_argument("-d", "--download_files", help="download files")
    parser.add_argument("-f", "--filesid", nargs="+", help="file id to download")
    parser.add_argument("-p", "--path", action="store", help="output file to download")
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')

    args = parser.parse_args()

    if args.my_histories:
        liste_histories(url, key)
    elif args.history_list:
        if args.name:
            files, idhisto = liste_historyfiles(args.key, args.url, args.name)
            for file in files:
                print files[file], file
        else:
            print "the -h option need a history name"
    elif args.name_workflow:
        run_workflow(args.key, args.url, args.name_workflow)
    elif args.download_files:
        if args.fileid:
            downloadfile(args.key, args.url, args.fileid, idhisto, args.path)
