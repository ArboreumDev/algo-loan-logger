# flake8: noqa E501
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


# https://github.com/algorandfoundation/ARCs/blob/main/ARCs/arc-0003.md#json-metadata-file-schema:
# full_nft_default_metadata = {
#     "title": "Token Metadata",
#     "type": "object",
#     "properties": {
#         "name": {
#             "type": "string",
#             "description": "Identifies the asset to which this token represents"
#         },
#         "decimals": {
#             "type": "integer",
#             "description": "The number of decimal places that the token amount should display - e.g. 18, means to divide the token amount by 1000000000000000000 to get its user representation."
#         },
#         "description": {
#             "type": "string",
#             "description": "Describes the asset to which this token represents"
#         },
#         "image": {
#             "type": "string",
#             "description": "A URI pointing to a file with MIME type image/* representing the asset to which this token represents. Consider making any images at a width between 320 and 1080 pixels and aspect ratio between 1.91:1 and 4:5 inclusive."
#         },
#         "image_integrity": {
#             "type": "string",
#             "description": "The SHA-256 digest of the file pointed by the URI image. The field value is a single SHA-256 integrity metadata as defined in the W3C subresource integrity specification (https://w3c.github.io/webappsec-subresource-integrity)."
#         },
#         "image_mimetype": {
#             "type": "string",
#             "description": "The MIME type of the file pointed by the URI image. MUST be of the form 'image/*'."
#         },
#         "background_color": {
#             "type": "string",
#             "description": "Background color do display the asset. MUST be a six-character hexadecimal without a pre-pended #."
#         },
#         "external_url": {
#             "type": "string",
#             "description": "A URI pointing to an external website presenting the asset."
#         },
#         "external_url_integrity": {
#             "type": "string",
#             "description": "The SHA-256 digest of the file pointed by the URI external_url. The field value is a single SHA-256 integrity metadata as defined in the W3C subresource integrity specification (https://w3c.github.io/webappsec-subresource-integrity)."
#         },
#         "external_url_mimetype": {
#             "type": "string",
#             "description": "The MIME type of the file pointed by the URI external_url. It is expected to be 'text/html' in almost all cases."
#         },
#         "animation_url": {
#             "type": "string",
#             "description": "A URI pointing to a multi-media file representing the asset."
#         },
#         "animation_url_integrity": {
#             "type": "string",
#             "description": "The SHA-256 digest of the file pointed by the URI external_url. The field value is a single SHA-256 integrity metadata as defined in the W3C subresource integrity specification (https://w3c.github.io/webappsec-subresource-integrity)."
#         },
#         "animation_url_mimetype": {
#             "type": "string",
#             "description": "The MIME type of the file pointed by the URI animation_url."
#         },
#         "properties": {
#             "type": "object",
#             "description": "Arbitrary properties (also called attributes). Values may be strings, numbers, object or arrays."
#         },
#         "extra_metadata": {
#             "type": "string",
#             "description": "Extra metadata in base64. If the field is specified (even if it is an empty string) the asset metadata (am) of the ASA is computed differently than if it is not specified."
#         },
#         "localization": {
#             "type": "object",
#             "required": ["uri", "default", "locales"],
#             "properties": {
#                 "uri": {
#                     "type": "string",
#                     "description": "The URI pattern to fetch localized data from. This URI should contain the substring `{locale}` which will be replaced with the appropriate locale value before sending the request."
#                 },
#                 "default": {
#                     "type": "string",
#                     "description": "The locale of the default data within the base JSON"
#                 },
#                 "locales": {
#                     "type": "array",
#                     "description": "The list of locales for which data is available. These locales should conform to those defined in the Unicode Common Locale Data Repository (http://cldr.unicode.org/)."
#                 },
#                 "integrity": {
#                     "type": "object",
#                     "patternProperties": {
#                         ".*": { "type": "string" }
#                     },
#                     "description": "The SHA-256 digests of the localized JSON files (except the default one). The field name is the locale. The field value is a single SHA-256 integrity metadata as defined in the W3C subresource integrity specification (https://w3c.github.io/webappsec-subresource-integrity)."
#                 }
#             }
#         }
#     }
# }
