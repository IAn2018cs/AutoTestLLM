# coding=utf-8

from tools import load_data
from uis.home.core import RoleInfo, start_gen

if __name__ == '__main__':
    # ai_model = 'gpt-4o-mini-2024-07-18-only-ai-two-conv'
    ai_model = 'gpt-4o-mini-2024-07-18-ai_poly25_two_conv'
    role_file = 'test_case/character.csv'
    dialogue_file = 'test_case/dialogue.csv'
    rounds = 10
    conv_length = 100
    open_translate = True

    role_list = load_data(role_file, ['Name', 'first_message', 'system'])
    roles = []
    for i, item in enumerate(role_list):
        roles.append(RoleInfo(
            role_id=i + 1,
            name=item['Name'],
            brief_intro=item['system'],
            first=item['first_message']
        ))
    dialogue_list = load_data(dialogue_file, ['content'])
    dialogue = []
    for item in dialogue_list:
        dialogue.append(item['content'])
    result_url = start_gen(ai_model, roles, dialogue, rounds, conv_length, open_translate)
    print(result_url)
