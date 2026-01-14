from models.sign_data import Sign,Class


def extractor(courses:list[Class]) -> list[Sign]:
    """返回status为1的未签到的"""
    result = []
    for course in courses:
        for sign in course.signs:
            if sign.status==1:
               result.append(sign)
    return result
def sort_sign(signs:list[Sign]) -> dict[str,list[Sign]]:
    """分类sign_id"""
    result = {"not_find_sign_id":[],"find_sign_id":[]}
    for sign in signs:
        if sign.sign_id:
            result["find_sign_id"].append(sign)
        else:
            result["not_find_sign_id"].append(sign)
    return result