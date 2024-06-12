from django.http import JsonResponse
from rest_framework.decorators import api_view

def is_code_function(code) -> bool:
    pass

def parse_function(code) -> tuple[str, list[str]]:
    pass

def convert_function(code) -> str:
    pass

def is_code_assignment(code) -> bool:
    pass

def convert_assignment(code) -> str:
    pass

def convert_to_python(code) -> str:
    if is_code_function(code):
        return convert_function(code)
    
    if is_code_assignment(code):
        return convert_assignment(code)
    
def run_code(code: str) -> str:
    pass


@api_view(['POST'])
def run_psuedocode(request):
    codeList = []
    print('DATA:', request.data)
    for code in request.data['code']:
        codeList.append(convert_to_python(code))

    codeString = ''
    for code in codeList:
        codeString += f'{code}\n'

    output = run_code(codeString)
    
    # temp, later will send output as response
    return JsonResponse({'res': output})