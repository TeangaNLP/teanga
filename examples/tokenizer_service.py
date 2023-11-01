from flask import Flask, request, jsonify, abort

app = Flask(__name__)

def token_indexes(text, token):
    i = 0
    while i < len(text):
        j = text.find(token, i)
        if j == -1:
            yield (i, len(text))
            i = len(text)
        else:
            yield (i, j)
            i = j + len(token)

@app.route('/tokenize', methods=['POST'])
def tokenize():
    data = request.get_json()
    text = data['text']
    tokens = {"tokens": list(token_indexes(text, " "))}
    return jsonify(tokens)

@app.route('/tokenize', methods=['GET'])
def meta():
    if request.query_string == b"produces":
        return jsonify({"tokens": {"type": "span", "on": "text"}})
    elif request.query_string == b"requires":
        return jsonify({"text": {"type": "characters"}})
    else:
        abort(404)

if __name__ == '__main__':
    app.run()

