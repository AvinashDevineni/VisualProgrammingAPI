import os
import shutil
import traceback
import random
import re

from django.http import JsonResponse
from rest_framework.decorators import api_view

_NAME_REGEX = r"[a-zA-Z_][a-zA-Z0-9_]*"

_CODE_BASE_DIR = 'prog_files'
_OUTPUT_FILE_VAR_NAME = 'outputFile' 
_MODULES = ['math']
_MIN_FOLDER_INT = -9999999
_MAX_FOLDER_INT = 9999999

def is_pseudocode_function(code: str) -> bool:
    return bool(re.match(_NAME_REGEX + r"\(.*\)", code))

'''
    TODO
    would be nice for the code returned from the list funcs to work
    for both lists and strings since the same naming makes sense,
    preventing names such as GET_AT_LIST or REMOVE_AT_STRING which
    would be annoying as a user
'''
def convert_function_pseudocode(code: str) -> str:
    codeIdx = 0

    funcName = ''
    while codeIdx < len(code):
        if code[codeIdx] == '(':
            codeIdx += 1
            break
        # .upper() to ensure all uppercase for match statement later
        funcName += code[codeIdx].upper()
        codeIdx += 1

    curFuncParam: str = ''
    inString = False # doesn't work properly when quotes are in a string

    # for error checking
    numOpeningParentheses = 0
    numClosingParentheses = 0

    funcParamsString: str = ''
    funcParamsList: list[str] = []
    numParams = 0
    while codeIdx < len(code) - 1: # - 1 because last char is )
        if code[codeIdx] == '(' and not inString:
            numOpeningParentheses += 1
        
        elif code[codeIdx] == ')' and not inString:
            numClosingParentheses += 1
        
        if code[codeIdx] == ',' and not inString:
            if is_pseudocode_function(curFuncParam):
                curFuncParam = convert_function_pseudocode(curFuncParam)
            
            funcParamsString += f"{curFuncParam}, "
            funcParamsList.append(curFuncParam)
            curFuncParam = ''
            numParams += 1

        elif inString or code[codeIdx] != ' ':
            curFuncParam += code[codeIdx]
        
        if code[codeIdx] == '"':
            inString = not inString

        codeIdx += 1

    if is_pseudocode_function(curFuncParam):
        curFuncParam = convert_function_pseudocode(curFuncParam)
    funcParamsString += curFuncParam
    funcParamsList.append(curFuncParam)
    numParams += 1

    parenthesesDiff = numOpeningParentheses - numClosingParentheses
    if parenthesesDiff > 0:
        raise SyntaxError(f"{parenthesesDiff} '(' {'was' if parenthesesDiff == 1 else 'were'} not closed.")
    
    elif parenthesesDiff < 0:
        raise SyntaxError(f"{-parenthesesDiff} ')' {'is' if parenthesesDiff == -1 else 'are'} unnecessary.")

    resCode = ''

    # functions with params
    numParamsAccepted = None # setting to none to check if func takes params
    try: # wrapping in try except bc of funcParamsList being accessed
        match funcName:
            #region Math Funcs
            #region Trig Funcs
            case 'COS':
                numParamsAccepted = 1
                resCode = f"math.cos({funcParamsString})"
            case 'SIN':
                numParamsAccepted = 1
                resCode = f"math.sin({funcParamsString})"
            case 'TAN':
                numParamsAccepted = 1
                resCode = f"math.tan({funcParamsString})"
            case 'ARC_COS':
                numParamsAccepted = 1
                return f"math.acos({funcParamsString})"
            case 'ARC_SIN':
                numParamsAccepted = 1
                resCode = f"math.asin({funcParamsString})"
            case 'ARC_TAN':
                numParamsAccepted = 1
                resCode = f"math.atan({funcParamsString})"
            #endregion
            
            case 'POWER':
                numParamsAccepted = 2
                resCode = f"math.pow({funcParamsString})"
            #endregion

            #region List Funcs
            case 'APPEND_TO': # 0 is list, 1 is val
                numParamsAccepted = 2
                resCode = f"{funcParamsList[0]}.append({funcParamsList[1]})"

            case 'REMOVE_FROM':
                numParamsAccepted = 1
                resCode = f"{funcParamsString} = {funcParamsString}[:-1]"

            case 'REMOVE_AT': # 0 is index, 1 is list
                numParamsAccepted = 2
                resCode = f"{funcParamsList[1]}.remove({funcParamsList[1]}[{funcParamsList[0]}])"

            case 'GET_FROM':
                numParamsAccepted = 1
                resCode = f"{funcParamsString}[len({funcParamsString}) - 1]"

            case 'GET_AT': # 0 is index, 1 is list
                numParamsAccepted = 2
                resCode = f"{funcParamsList[1]}[{funcParamsList[0]}]"
            #endregion

            case 'PRINT':
                numParamsAccepted = 1
                resCode = f"print({funcParamsString}, file={_OUTPUT_FILE_VAR_NAME})"

    except IndexError:
        raise TypeError(f"{funcName} takes "\
                        f"{numParamsAccepted} {'argument' if numParamsAccepted == 1 else 'arguments'}. "\
                        f"{numParams} {'was' if numParams == 1 else 'were'} passed.")
    
    # checking if != None bc a valid func may not take params
    if numParamsAccepted != None and numParamsAccepted != numParams:
        raise TypeError(f"{funcName} takes "\
                        f"{numParamsAccepted} {'argument' if numParamsAccepted == 1 else 'arguments'}. "\
                        f"{numParams} {'was' if numParams == 1 else 'were'} passed.")

    # functions with no params
    isNoParamFunc = False
    match funcName:
        #region Math Funcs
        case 'EULER':
            isNoParamFunc = True
            resCode = 'math.e'
        case 'PI':
            isNoParamFunc = True
            resCode = 'math.pi'
        #endregion

    if isNoParamFunc and funcParamsString != '':
        raise TypeError(f"{funcName} takes no arguments. "\
                        f"{numParams} {'was' if numParams == 1 else 'were'} passed.")

    if resCode == '':
        raise NameError(f"{funcName} is not a defined function.")

    return resCode
    
def is_pseudocode_assignment(code: str) -> bool:
    # allows rhs of assignment to be anything
    # also allows multiple equal signs
    return bool(re.match(_NAME_REGEX + r"\s*=\s*.*", code))

def convert_assignment_pseudocode(code: str) -> str:
    codeIdx = 0

    varName = ''
    while codeIdx < len(code):
        if code[codeIdx] == '=':
            codeIdx += 1
            break
        elif code[codeIdx] != ' ':
            varName += code[codeIdx]

        codeIdx += 1

    assignmentVal = ''
    while codeIdx < len(code):
        if code[codeIdx] != ' ':
            assignmentVal += code[codeIdx]

        codeIdx += 1

    if is_pseudocode_function(assignmentVal):
        assignmentVal = convert_function_pseudocode(assignmentVal)

    return f"{varName} = {assignmentVal}"

def convert_to_python(code: str) -> str:
    if is_pseudocode_function(code):
        return convert_function_pseudocode(code)
    
    if is_pseudocode_assignment(code):
        return convert_assignment_pseudocode(code)

def run_code(code: str) -> str:
    folderPath = random.randint(_MIN_FOLDER_INT, _MAX_FOLDER_INT)
    folderPath = os.path.join(_CODE_BASE_DIR, str(folderPath))
    while (os.path.isdir(folderPath)):
        folderPath = random.randint(_MIN_FOLDER_INT, _MAX_FOLDER_INT)
        folderPath = os.path.join(_CODE_BASE_DIR, str(folderPath))

    os.mkdir(folderPath)

    PY_FILE = os.path.join(folderPath, 'user_code.py')
    OUTPUT_FILE = os.path.join(folderPath, 'output.txt')

    with open(PY_FILE, 'w') as pyFile:
        for module in _MODULES: # importing required modules
            pyFile.write(f"import {module}\n")

        pyFile.write(f"{_OUTPUT_FILE_VAR_NAME} = open(r\"{OUTPUT_FILE}\", 'w')\n") # for print func
        pyFile.write(f"{code}\n")
        pyFile.write(f"{_OUTPUT_FILE_VAR_NAME}.close()")

    open(OUTPUT_FILE, 'x').close()

    try:
        with open(PY_FILE) as userCode:
            exec(userCode.read())
    except Exception:
        traceback.print_exc()

    output = ''
    with open(OUTPUT_FILE) as outputFile:
        for line in outputFile.readlines():
            output += line

    #shutil.rmtree(folderPath)

    return output

@api_view(['POST'])
def run_pseudocode(request):
    convertedCode = ''
    for code in request.data['code']:
        convertedCode += f"{convert_to_python(code)}\n"

    output = run_code(convertedCode)
    
    return JsonResponse({'res': output})