import json
import re
import sys

import requests
import urllib3

urllib3.disable_warnings()


def get_url_ip(url):
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,en-GB;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Pragma': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/555.0 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/555.0 Edg/105.0.0.0',
    }

    params = {
        'lang': 'zh-CN',
    }

    response = requests.get(f'http://ip-api.com/json/{url}', headers=headers, params=params, verify=False)

    try:
        return response.json()
    except Exception as e:
        print(f'Error => get_url_ip[{url}]', e, response.text)
        return response.text


def get_github_ips():
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7,en-GB;q=0.6',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'DNT': '1',
        'Pragma': 'no-cache',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/555.0 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/555.0 Edg/105.0.0.0',
    }

    response = requests.get('https://raw.hellogithub.com/hosts', headers=headers, verify=False)
    if response.status_code == 200:
        return response.text
    else:
        return ''


def operate_custom_host(operate_type: str = 'get', hosts: list = None):
    """
    获取或更新自定义hosts
    :param operate_type: 'get' | 'set'
    :param hosts: list
    :return:
    """
    if hosts is None:
        hosts = []
    try:
        if operate_type == 'set':
            hosts = json.dumps(hosts)
    except:
        raise ValueError('hosts 格式错误，应为列表，如：["127.0.0.1 domain.dev"]')

    headers = {
        'Host': 'www.gorouter.info',
        'Connection': 'keep-alive',
        'Pragma': 'no-cache',
        'Cache-Control': 'no-cache',
        'Accept': '*/*',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/555.0 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/555.0 Edg/105.0.0.0',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://s.miwifi.com',
        'X-Requested-With': 'com.xiaomi.smarthome',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://s.miwifi.com/',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7',
    }

    is_set_operate = operate_type == 'set'

    request_url = f'https://www.gorouter.info/api-third-party/service/internal/custom_host_{operate_type}'

    if is_set_operate:
        response = requests.post(request_url, headers=headers, data={**base_data, 'hosts': hosts}, verify=False)
    else:
        response = requests.get(request_url, headers=headers, params=base_data, verify=False)

    try:
        return response.json()
    except Exception as e:
        print(f'Error => operate_custom_host[{operate_type}]', e, response.text)
        return response.text


def cover_ip(hosts):
    for i in range(len(hosts)):
        item = hosts[i]
        if not re.match(r'^127\.0\.0\.1', item):
            item_temp = item.split(' ')
            item_url = item_temp[-1]
            res = get_url_ip(item_url)
            ip = res.get('query', '') if type(res) == dict else ''
            if ip:
                hosts[i] = f'{ip} {item_url}'
    return hosts


if __name__ == '__main__':
    base_data = sys.argv[1]
    try:
        base_data = json.loads(base_data)
    except:
        raise ValueError(
            '请配置正确的 base_data 参数，如 \'{"appId": "xxx", "deviceId": "xxx", "clientId": "xxx", "scope": "xxx", "token": "xxx"}\'')

    # 设置hosts时，注释会被忽略掉
    new_custom_hosts = [
        # "127.0.0.1 le.dev",
        # "104.16.85.20 cdn.jsdelivr.net",
        # "127.0.0.1 le.dev.com # test",  # " # test" 这部分会被忽略
        # "# xxx",  # 整行会被忽略
    ]
    
    get_custom_hosts_res = operate_custom_host('get')
    if type(get_custom_hosts_res) != dict or get_custom_hosts_res.get('code', -1) != 0:
        print('更新异常 => ', get_custom_hosts_res)
        exit(-1)

    custom_hosts = get_custom_hosts_res.get('hosts', [])
    github_ips_start = '127.0.0.1 le.github-ips.start'
    github_ips_end = '127.0.0.1 le.github-ips.end'

    # print('custom_hosts => ', json.dumps(custom_hosts, indent=2))
    try:
        if custom_hosts.index(github_ips_start) >= 0:
            # 删除旧 github_ips 内容
            del custom_hosts[
                custom_hosts.index(github_ips_start):custom_hosts.index(github_ips_end) + 1]
    except:
        pass

    custom_hosts = cover_ip(custom_hosts)
    # print('new custom_hosts => ', json.dumps(custom_hosts, indent=2))

    github_ips = list(filter(lambda x: re.match(r'^\d', x), get_github_ips().split('\n')))
    print('github_ips => ', json.dumps(github_ips, indent=2))
    github_ips = cover_ip(github_ips)
    print('new github_ips => ', json.dumps(github_ips, indent=2))

    # 添加 github_ips 内容的开始、结束元素，方便下次仅更新 github_ips 部分的内容
    github_ips.insert(0, github_ips_start)
    github_ips.insert(len(github_ips) + 1, github_ips_end)
    new_custom_hosts.extend(custom_hosts)
    new_custom_hosts.extend(github_ips)
    print('更新结果 => ', operate_custom_host('set', new_custom_hosts))
