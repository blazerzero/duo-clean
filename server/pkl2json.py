import json
import pickle
import os
import helpers

def pkl2jsonRecursive():
    project_ids = os.listdir('./docker-out/')
    for project_id in project_ids:
        files = os.listdir('./docker-out/' + project_id + '/')
        for f in files:
            print('./docker-out/' + project_id + '/' + f)
            if '.p' in f:
                obj = pickle.load( open('./docker-out/' + project_id + '/' + f, 'rb') )
                if type(obj) == dict:
                    if f == 'fd_metadata.p':
                        for k in obj.keys():
                            obj[k] = obj[k].asdict()
                    elif f == 'interaction_metadata.p':
                        for idx in obj['feedback_history'].keys():
                            for col in obj['feedback_history'][idx].keys():
                                obj['feedback_history'][idx][col] = [i.asdict() for i in obj['feedback_history'][idx][col]]
                        obj['sample_history'] = [i.asdict() for i in obj['sample_history']]
                    elif f == 'study_metrics.p':
                        for idx in obj.keys():
                            obj[idx] = [i.asdict() for i in obj[idx]]

                    with open('./docker-out/' + project_id + '/' + f.split('.')[0] + '.json', 'w') as fp:
                        json.dump(obj, fp, ensure_ascii=False, indent=4)

if __name__ == '__main__':
    pkl2jsonRecursive()