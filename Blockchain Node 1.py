import datetime
from flask import Flask,request    
import json                         #to convert a dictionary entity into json
import hashlib                      #to calculate the hash value of given data
from urllib.parse import urlparse   #to parse an url and pick the ip address
#to generate a request for an i.p address using python script
import requests                    

#class to contain whole blockchain protocol
class Blockchain:   
    #constructor or initiliser to initilise chain from a genesis block
    def __init__(self):            
       self.chain = [] #initise the chain
       self.transactions = []
       #genesis block
       self.create_block(nonce=1,previous_hash = 0) 
       #set to collect the info about other nodes in the network
       self.nodes = set() 
       
    def create_block(self,nonce,previous_hash): #create block method
        block = {'index' : len(self.chain)+1,
                 'timestamp' : str(datetime.datetime.now()),
                 'nonce' : nonce,
                 'transactions' : self.transactions,
                 'previous_hash' : previous_hash} 
        #define structure or element that a block can contain
        self.transactions = []
        self.chain.append(block)
        return block
    
    #get chain method
    def get_chain(self): 
        #returns a list containing chain or an array of chain  
        return self.chain  

    def hash(self,block):
        encoded_block = json.dumps(block , sort_keys=True).encode()
        return hashlib.sha256(encoded_block).hexdigest()

    def proof_of_work(self,previous_nonce):
        new_nonce = 1
        check_nonce = False
        while check_nonce != True:
            hash_val = hashlib.sha256(str(new_nonce**2 - previous_nonce**2).encode()).hexdigest()
            if hash_val[0:4] == '0000':
                check_nonce = True
            else:
                new_nonce += 1
        return new_nonce
    
    def add_transactions(self,Deliver_By,Receiver,
                         Capacity,ID_No,Remarks):      
        self.transactions.append({
                                  'Deliver_By' : Deliver_By,
                                  'Receiver' : Receiver,
                                  'Capacity' : Capacity,
                                  'ID_No' : ID_No,
                                  'Remarks' : Remarks})
        previous_block_index = self.chain[-1]['index'] + 1
        return previous_block_index

    def is_chain_valid(self,chain):   
        prev_block  = chain[0]
        blk_index = 1
        while blk_index < len(chain):
            current_block = chain[blk_index]
            #current_block previous should be same as hash of previous block
            if current_block['previous_hash'] != self.hash(prev_block):   
                return False
            #Checking whether a chain is using the common POW
            prev_nonce = prev_block['nonce']           #0,1,2
            current_nonce = current_block['nonce']     #1,2,3
            hash_val = hashlib.sha256(str(current_nonce**2 - prev_nonce**2).encode()).hexdigest()
            if hash_val[:4] != '0000':
                return False          
            prev_block = current_block
            blk_index += 1
        return True

    #Method to add Nodes into the network
    def add_node(self,address):
        parsed_url = urlparse(address).netloc
        self.nodes.add(parsed_url)

    #Replace chain method in case any other node is having larger chain
    def replace_chain(self):
        network = self.nodes
        max_length = len(self.chain)
        longest_chain = None
        for node in network:
            response = requests.get(f'http://{node}/view_chain')
            if response.status_code == 200:
                chain = response.json()['Chain']
                length = len(chain)
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True              
        return False                    
    
blk = Blockchain()     #instance of the class
app = Flask(__name__)  #instance for flask

@app.route('/mine_block')           
def mine_block():
    previous_block = blk.chain[-1]
    nonce = blk.proof_of_work(previous_block['nonce'])    
    previous_hash = blk.hash(previous_block)
    block = blk.create_block(nonce,previous_hash)      
    response = {'Block' : block,
                'Hash_Value' : blk.hash(block)} 
    #response with block created
    return response                             

@app.route('/view_chain')            
def view_chain():    
    Chain = blk.get_chain()          
    response = {'Chain' : Chain} 
    #response with the chain available
    return response                 

@app.route('/request_transaction' , methods=['POST'])
def request_transaction():
    d = request.form['Deliver_By']         
    r = request.form['Receiver']      
    c = request.form['Capacity']         
    i = request.form['ID_No']
    rm = request.form['Remarks']
    idx = blk.add_transactions(d,r,c,i,rm)
    response = {'Response' : f'Transaction added for block number {idx}'}
    return response

@app.route('/is_valid')
def is_valid():
    status = blk.is_chain_valid(blk.chain)
    if status == True:
        response = {'Message' : 'Chain is Valid' }
    else:
        response = {'Message' : 'Chain is Invalid' }
    return response

@app.route('/connect_nodes' , methods=['POST'])
def connect_nodes():
    json = request.get_json() 
    #fetch the node address to connect together given in json format
    nodes = json.get("nodes")
    if nodes is None:
        return "No Nodes",400
    else:
        for node in nodes:
            blk.add_node(node)
    response = {'Message' : 'All nodes are connected',
                'Total Nodes' : list(blk.nodes)}               
    return response

@app.route('/update_chain')
def update_chain():
    is_chain_replaced = blk.replace_chain()
    if is_chain_replaced == True:
        response = {'Message' : 'The chain is replaced with largest chain',
                    'New chain' : blk.chain}
    else:
        response = {'Message' : 'The chain is itself the longest one',
                    'Existing chain' : blk.chain}
    return response     
app.run(host='0.0.0.0',port=5001) #trigger the flask          