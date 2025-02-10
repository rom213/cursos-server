from celery import Celery

celery = Celery('app', broker='redis://localhost:6379/0')

@celery.task
def remove_member_task(group_email, member_email, access_token):
    url = f'https://admin.googleapis.com/admin/directory/v1/groups/{group_email}/members/{member_email}'
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    response = requests.delete(url, headers=headers)
    
    if response.status_code == 204:
        print(f"Miembro {member_email} eliminado con éxito del grupo {group_email}.")
        return True
    else:
        print(f"Error al eliminar el miembro: {response.status_code}")
        return False
