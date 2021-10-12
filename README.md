# algo-loan-logger
microservice to be used to 
1) log loan-related data onto the algorand blockchain by 
  - creating NFTs with loan-data as token-metadata
  - creating transactions from token-owner to token-owner writing arbitrary-data into the note-field of the tx
2) return all logs/notes related to created asset


## 0) Preparation
You will need to have a local blockchain running to test most of the stuff, so you will need to install basic algorand 
support.
## connecting to a node

this required me some fiddling around and I cant retrace the exact steps that worked for me.
The goal should be to have a local node network runnning on your PC of which you need to know
- the algod-address: Usually localhost:4001
- the algod-toekn: Usually a bunch of "aaaaa..."
- the master-mnemonic: a passphrase for an acconut on the network that holds (preferably a lot) of algos. Its 24 words from which a private/public key pair can be derived

Maybe the master-mnemonic needs to be exported using  `goal`-cli tool (see troubleshooting section below)
### how to start local chain

follow instructions [here](https://github.com/scale-it/algo-builder/tree/master/infrastructure) to set up a local network
that you can then start with

> make create-private-net

this didnt immediately work for me, now I am doing this:

> (tenv) ➜  infrastructure git:(develop) ✗ goal network start -r ./node_data

### how to start local chain using the sandbox

cd to algobuilder/infrastructure

> make sandbox-up

later:
> make sandbox-down

## 1) Setup

#### 1.1 create a .env file
see `example.env` and fill in the mnemonics from your local blockchain & the token for the purestake.io API

#### 1.2 virtual environment

a local virtual env running python version 3.8

e.g. using `virtualenv` -library:

setup virtualenv (e.g named 'algo-env') and point it to your local executable of python 3.8 like this:

> virtualenv algo-env --python=/usr/bin/python3.8
> source algo-env/bin/activate
> pip install -r requirememts.txt
> pip install -r requirememts-dev.txt

#### 1.3 add /app-directory to your pythonpath

e.g. like described [here](https://code.visualstudio.com/docs/python/environments#_use-of-the-pythonpath-variable) (<-vscode)

## 2) Run API
#### local mode

> make dev-api-local

then check out the docs at http://localhost:8000/docs

#### as a docker-container
TODO

##  3) Test

> make test-local


## 3) TROUBLESHOOTING

#### getting the mnemonic from a local network
this should work for the local network but can also be done for the sandbox
(for the lattter, you probably need to prefix the command with `.sandbox` and maybe the first step is not neccessary)

0) cd to /infrastructure / wherever you installed sandbox

1) first export network data root so that goal commands need not always specify with -d flag
> export ALGORAND_DATA="$HOME/net1/Primary"

2) get master account address
>  algorand goal account list                                                              

3) export mnemonic:
> algorand goal account export -a J2NMTNR45TSYHIMSTJL7RLREZD4AIZUVVG77N2G4RBCEVOCVVW2NQEU2ME
> >>>: please price excite wash exit news hybrid cool hurdle athlete transfer giggle ...

