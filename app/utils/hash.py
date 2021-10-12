# how to hash with extra metadata, in case this should be verified by a smart-contract?
import base64
import hashlib

extra_metadata_base64 = "iHcUslDaL/jEM/oTxqEX++4CS8o3+IZp7/V5Rgchqwc="
extra_metadata = base64.b64decode(extra_metadata_base64)
json_metadata = """{
    "name": "My Picture",
    "description": "Lorem ipsum...",
    "image": "https://s3.amazonaws.com/your-bucket/images/{id}.png",
    "image_integrity": "sha256-47DEQpj8HBSa+/TImW+5JCeuQeRkm5NMpJWZG3hSuFU=",
    "image_mimetype": "image/png",
    "external_url": "https://mysongs.com/song/{id}",
    "extra_metadata": "iHcUslDaL/jEM/oTxqEX++4CS8o3+IZp7/V5Rgchqwc="
}"""

h = hashlib.new("sha512_256")
h.update(b"arc0003/amj")
h.update(json_metadata.encode("utf-8"))
json_metadata_hash = h.digest()

h = hashlib.new("sha512_256")
h.update(b"arc0003/am")
h.update(json_metadata_hash)
h.update(extra_metadata)
am = h.digest()

print("Asset metadata in base64: ")
print(base64.b64encode(am).decode("utf-8"))