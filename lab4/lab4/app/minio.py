from django.conf import settings
from minio import Minio
from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import Response

def process_file_upload(file_object: InMemoryUploadedFile, client, image_name):
    try:
        client.put_object('lab1', image_name, file_object, file_object.size)
        return f"http://localhost:9000/lab1/{image_name}"
    except Exception as e:
        return {"error": str(e)}

def add_pic(new_word_card, pic):
    client = Minio(           
            endpoint=settings.AWS_S3_ENDPOINT_URL,
           access_key=settings.AWS_ACCESS_KEY_ID,
           secret_key=settings.AWS_SECRET_ACCESS_KEY,
           secure=settings.MINIO_USE_SSL
    )
    i = new_word_card.word
    img_obj_name = f"{i}.png"

    if not pic:
        return Response({"error": "Нет файла для изображения логотипа."})
    result = process_file_upload(pic, client, img_obj_name)

    if 'error' in result:
        return Response(result)

    new_word_card.word_image = result
    new_word_card.save()

    return Response({"message": "success"})


def delete_pic(word_card):
    client = Minio(           
            endpoint=settings.AWS_S3_ENDPOINT_URL,
           access_key=settings.AWS_ACCESS_KEY_ID,
           secret_key=settings.AWS_SECRET_ACCESS_KEY,
           secure=settings.MINIO_USE_SSL
    )
    name = word_card.word
    img_obj_name = f"{name}.png"
    client.remove_object(settings.AWS_STORAGE_BUCKET_NAME, img_obj_name)

    