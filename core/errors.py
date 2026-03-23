ERRORS = {
    'already_exist_mail': {
        'code': '0001',
        'message': 'El correo ya ha sido registrado previamente'
    }, 
    'invalid_permission': {
        'code': '0002',
        'message': 'Permisos no validos para el perfil seleccionado'
    }, 
    'user_info_is_missing': {
        'code': '0003',
        'message': 'Informacion del usuario incompleta (birthdate, genero, phone, rfc)'
    }, 
    'permission_denied': {
        'code': '0004',
        'message': 'No cuentas con el permiso para realizar esta accion'
    }, 
    'bad_format_date': {
        'code': '0005',
        'message': 'La fecha tiene un formato erroneo (dd/mm/aaaa)'
    }, 
    'org_does_not_exist': {
        'code': '0006',
        'message': 'La organizacion no existe'
    },
    'profile_notfound': {
        'code': '0007',
        'message': 'Perfil no encontrado'
    }, 
    'permission_notfound': {
        'code': '0008',
        'message': 'No se encontraron permisos para el usuario solicitado'
    }, 
    'invalid_token': {
        'code': '0009',
        'message': 'Token Invalido '
    }, 
    'org_does_not_included': {
        'code': '0010',
        'message': 'No se incluyo la organizacion en el request'
    }, 
    'prerrequisite_does_not_exist': {
        'code': '0011',
        'message': 'El pre-registro no existe'
    }, 
    'prerrequisite_does_not_valid': {
        'code': '0012',
        'message': 'El pre-registro ya ha sido activado'
    }, 
    'integrity_error': {
        'code': '0013',
        'message': 'Ha ocurrido un error de integridad en los datos, revise los datos'
    }, 
    'database_error': {
        'code': '0014',
        'message': 'Ha ocurrido un error en la de base de datos, revise los datos'
    }, 
    'max_user_number_reached': {
        'code': '0015',
        'message': 'Has alcanzado el máximo numero de usuarios para este plan'
    }, 
    'record_already_exist': {
        'code': '0016',
        'message': 'El registro ya existe en la base de datos'
    }, 
    'bad_request': {
        'code': '0017',
        'message': 'No se incluyeron los datos necesarios para procesar la peticion'
    }, 
    'invalid_user_password': {
        'code': '0018',
        'message': 'Usuario y/o contraseña incorrectos'
    }, 
    'invalid_org': {
        'code': '0019',
        'message': 'Usuario no pertence a la organizacion'
    }, 
    'error_saved_info_saam': {
        'code': '0020',
        'message': 'Error al guardar la informacion en saam'
    },
    'not_match_password': {
        'code': '0021',
        'message': 'Las contraseñas no coinciden'
    },
    'user_notpermitted': {
        'code': '0022',
        'message': 'El usuario no corresponde a su perfil de ingreso'
    },
} 

def get_error(key):
    try:
        return "{}-{}".format(ERRORS[key]['code'],ERRORS[key]['message'])
    except Exception as e:
        print('Cannot  get error =>', str(e))
        return None