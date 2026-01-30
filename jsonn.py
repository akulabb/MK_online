import json

a = (6, 7)
str_a = json.dump(a)   #'[6, 7]'

b = json.loads(str_a)  #[6, 7]
