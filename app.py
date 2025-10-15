from flask import Flask, render_template, request, send_file
from io import BytesIO
import heapq

app = Flask(__name__)

# ---------- Huffman Node ----------
class Node:
    def __init__(self, byte, freq=0):
        self.byte = byte
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

# ---------- Build Huffman Tree ----------
def build_tree(freq_table):
    heap = [Node(b, f) for b, f in enumerate(freq_table) if f > 0]
    heapq.heapify(heap)
    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        parent = Node(0, left.freq + right.freq)
        parent.left = left
        parent.right = right
        heapq.heappush(heap, parent)
    return heap[0] if heap else None

# ---------- Generate Codes ----------
def generate_codes(root):
    codes = [''] * 256
    def dfs(node, code):
        if not node:
            return
        if not node.left and not node.right:
            codes[node.byte] = code
            return
        dfs(node.left, code + '0')
        dfs(node.right, code + '1')
    dfs(root, '')
    return codes

# ---------- Encode ----------
def compress_data(data):
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    root = build_tree(freq)
    codes = generate_codes(root)

    # Encode bits
    bits = ''
    for b in data:
        bits += codes[b]
    padding = (8 - len(bits) % 8) % 8
    bits += '0' * padding

    encoded_bytes = bytearray()
    for i in range(0, len(bits), 8):
        encoded_bytes.append(int(bits[i:i+8], 2))

    # Prepend frequency table (256 * 4 bytes)
    freq_bytes = b''.join(f.to_bytes(4, 'little') for f in freq)
    return freq_bytes + encoded_bytes + bytes([padding])

# ---------- Decode ----------
def decompress_data(huff_bytes):
    freq = [int.from_bytes(huff_bytes[i*4:i*4+4], 'little') for i in range(256)]
    root = build_tree(freq)

    data_bytes = huff_bytes[256*4:-1]
    padding = huff_bytes[-1]

    bits = ''
    for b in data_bytes:
        bits += f'{b:08b}'
    bits = bits[:-padding] if padding else bits

    result = bytearray()
    node = root
    for bit in bits:
        node = node.right if bit=='1' else node.left
        if not node.left and not node.right:
            result.append(node.byte)
            node = root
    return result

# ---------- Routes ----------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compress', methods=['POST'])
def compress_file():
    file = request.files['file']
    data = file.read()
    compressed = compress_data(data)
    return send_file(BytesIO(compressed), download_name=file.filename + '.huff', as_attachment=True)

@app.route('/decompress', methods=['POST'])
def decompress_file():
    file = request.files['file']
    data = file.read()
    decompressed = decompress_data(data)
    return send_file(BytesIO(decompressed), download_name=file.filename.replace('.huff',''), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
