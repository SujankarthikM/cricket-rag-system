from google.generativeai import client

client.configure(api_key="AIzaSyC7bAVtdapVd9HuyhCKk89KLwJhcg0c1IE")
info = client.api_key_info()

print(info)
