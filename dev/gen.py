import json,httpx

o = {}
for v in range(1,26+1):
    dv = (v-1) if not v % 2 else v
    print(dv,v)
    try: r = httpx.head(f'https://github.com/kaitz/fxcm/releases/tag/v{dv}').status_code
    except: r = httpx.head(f'https://github.com/kaitz/fxcm/releases/tag/v{dv}').status_code
    if r == 404:
        dv = input('dv: ').strip('/').split('/')[-1].strip('v')
        if not dv: continue
    o[f'fxcm_v{v}'] = {
        'p':f'fxcm_v{v}.exe',
        'fs':[[f'https://github.com/kaitz/fxcm/releases/download/v{dv}/fxcmv{v}.exe',f'fxcm_v{v}.exe']]
    }

o = json.dumps(o,ensure_ascii=False,separators=(',',':'),indent=4).replace(
                '\n            {',           '{').replace(
                '\n            [',           '[').replace(
                '\n            }\n        ]','\n        }]').replace(
                '\n            ]\n        ]','\n        ]]').replace(
                '\n            ',          '\n        ')
print(o[1:-2] + ',')
