from flask import Flask, render_template, jsonify
from pymongo import MongoClient

app = Flask(__name__)
collection = MongoClient()['local']['traceroute']


@app.route('/')
def index():
    return render_template("sankey.html")


class Node:
    def __init__(self, path, type):
        self.path = path
        self.type = type


@app.route('/data')
def data():
    nodes = {}
    paths = {}
    res = {'nodes': [], 'links': []}
    for i, post in enumerate(collection.find()):
        results = post['trace_result']

        #Add head node
        ip = results[0]['ip']
        if ip in nodes:
            nodes[ip].path = nodes[ip].path + " p" + str(i)
        else:
            nodes[ip] = Node("p" + str(i), 0)

        #Add tail node
        ip = results[len(results)-1]['ip']
        if ip in nodes:
            nodes[ip].path = nodes[ip].path + " p" + str(i)
        else:
            nodes[ip] = Node("p" + str(i), 1)

        #Add middle node
        for j in range(1, len(results)-1):
            ip = results[j]['ip']
            if ip != '*':
                if ip in nodes:
                    nodes[ip].path = nodes[ip].path + " p" + str(i)
                else:
                    nodes[ip] = Node("p" + str(i), 2)
            else:
                ip = "b%d.%d" % (i, j)
                if ip in nodes:
                    nodes[ip].path = nodes[ip].path + " p" + str(i)
                else:
                    nodes[ip] = Node("p" + str(i), 3)


        source = list(nodes.keys()).index(results[0]['ip'])

        for j in range(1, len(results)):
            if results[j]['ip'] != '*':
                ip = results[j]['ip']
            else:
                ip = "b%d.%d" % (i, j)
            target = list(nodes.keys()).index(ip)
            key = str(source) + '/' + str(target)
            if key in paths:
                paths[key] = paths[key] + " p" + str(i)
            else:
                paths[key] = "p" + str(i)
            source = target

    for i, (k, v) in enumerate(nodes.items()):
        item = {'id': i, 'name': k, 'path': v.path, 'type':v.type}
        res['nodes'].append(item)

    for k, v in paths.items():
        source, target = k.split('/')
        item = {'source': int(source), 'target': int(target), 'path': v, 'type': None, 'rtt': 1}
        res['links'].append(item)

    return jsonify(res)


if __name__ == '__main__':
    app.run()
