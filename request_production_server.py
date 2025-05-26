import requests

url = "https://5bmz7vm4galqb4-7860.proxy.runpod.net/tryon/"
files = {
    "model_image": open("/home/dci-admin/Documents/virtual_tryon_shopify/model.jpg", "rb"),
    "cloth_image": open("/home/dci-admin/Documents/virtual_tryon_shopify/cloth.jpg", "rb")
}
data = {
    "sample": 2,
    "scale": 2.0
}

response = requests.post(url, files=files, data=data)
print(response.json())