import nltk
import pickle
from nltk.chunk import named_entity

fl = 'C:\\nltk_data\\chunkers\\maxent_ne_chunker\\PY3\\english_ace_multiclass.pickle'

#with open(fl, "rb") as f:
#    chunker = pickle.load(f)


print("....................................")
 

document = """
    With conda, you can create, export, list, remove, and update environments 
    that have different versions of Python and/or packages installed in them. 
    Switching or moving between environments is called activating the 
    environment. You can also share an environment file.
    """

stop = nltk.corpus.stopwords.words('english')

document = ' '.join([i for i in document.split() if i not in stop])
sentences = nltk.tokenize.sent_tokenize(document)
sentences = [nltk.word_tokenize(sent) for sent in sentences]
sentences = [nltk.pos_tag(sent) for sent in sentences]

print(sentences)

names = []
for tagged_sentence in sentences:
    try:
        #chunks = chunker.parse(tagged_sentence)
        print("------------------------------------------------")
        chunks = nltk.ne_chunk(tagged_sentence)
        print("------------------------------------------------")
    except Exception as e:
        print(e)
    for chunk in chunks:
        if type(chunk) == nltk.tree.Tree:
            if chunk.label() == 'PERSON':
                names.append(' '.join([c[0] for c in chunk]))