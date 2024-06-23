from jmcomic import *
from jmcomic.cl import JmcomicUI

# 下方填入你要下载的本子的id，一行一个，每行的首尾可以有空白字符
jm_albums = '''
54747
28650
27512
20348
47729
61257
80358
18212
488125
485870
181611
89218
467180
480142
142464
273943
401574
231692
306848
371570
481979
190447
409896
384297
485647
495256
271249
74891
2868
441594
230702
284185
86779
478437
21994
502132
225764
352727
151696
391894
392101
428347
428348
148624
370634
442137
438000
467110
145289
505253
101792
371631
305291
427706
151607
505048
505484
369504
501838
451610
508253
355659
480841
58267
69354
221659
511010
145289
498750
371875
465335
39509
513984
452699
509489
377532
517500
218796
481536
515569
445794
248646
326357
241726
281142
290391
329995
429322
411613
318731
308472
105854
114445
98669
73451
98509
46555
27701
20106
4333
2388
122333
397150
394523
385372
362197
346346
305428
2057
333722
220455
148486
486253
477990
453931
452501
343898
334554
318730
310176
472952
203446
77778
410841
412004
149906
374495
346862
315728
330006
290455
122427
235366
265236
271249
278032
487798
382336
255015
230806
454803
481979
434801
434797
415513
477029
468624
380052
269417
527354
448098
509834
207063
293867
192957
529468
209232
181107
135697
107184
127282
441189
409658
116157
395281
395280
392326
469738
537119
542252
62268
543247
368837
401496
544360
544401
533552
549168
471872
547590
505241
392326
476677
223153
21407
533458
482542
433023
397478
550176
125237
104738
293593
303683
291407
149578
124561
78665
158
120944
2620
45159
13660
62202
262147
551529
97909
239027
245952
187
219
224
878
877
759
641
610
638
96125
390353
263104
421450
543081
484683
322028
303714
348168
436635
417463
245189
523276
443170
524360
389479
224879
475378
480111
411330
193267
355659
345433
278435
104274
435425
417420
275503
342584
320765
196775
229537
85055
554413
541285
368639
140620
21274
20902
545733
541762
543525
247044
55427
251050
220995
33775
308595
306326
50514
268453
266615
249121
451603
435777
355019
258778
220996
142568
124116
22392
479907
239797
495051
501638
398569
373099
138809
'''

# 单独下载章节
jm_photos = '''



'''


def env(name, default, trim=('[]', '""', "''")):
    import os
    value = os.getenv(name, None)
    if value is None or value == '':
        return default

    for pair in trim:
        if value.startswith(pair[0]) and value.endswith(pair[1]):
            value = value[1:-1]

    return value


def get_id_set(env_name, given):
    aid_set = set()
    for text in [
        given,
        (env(env_name, '')).replace('-', '\n'),
    ]:
        aid_set.update(str_to_set(text))

    return aid_set


def main():
    album_id_set = get_id_set('JM_ALBUM_IDS', jm_albums)
    photo_id_set = get_id_set('JM_PHOTO_IDS', jm_photos)

    helper = JmcomicUI()
    helper.album_id_list = list(album_id_set)
    helper.photo_id_list = list(photo_id_set)

    option = get_option()
    helper.run(option)
    option.call_all_plugin('after_download')


def get_option():
    # 读取 option 配置文件
    option = create_option(os.path.abspath(os.path.join(__file__, '../../assets/option/option_workflow_download.yml')))

    # 支持工作流覆盖配置文件的配置
    cover_option_config(option)

    # 把请求错误的html下载到文件，方便GitHub Actions下载查看日志
    log_before_raise()

    return option


def cover_option_config(option: JmOption):
    dir_rule = env('DIR_RULE', None)
    if dir_rule is not None:
        the_old = option.dir_rule
        the_new = DirRule(dir_rule, base_dir=the_old.base_dir)
        option.dir_rule = the_new

    impl = env('CLIENT_IMPL', None)
    if impl is not None:
        option.client.impl = impl

    suffix = env('IMAGE_SUFFIX', None)
    if suffix is not None:
        option.download.image.suffix = fix_suffix(suffix)


def log_before_raise():
    jm_download_dir = env('JM_DOWNLOAD_DIR', workspace())
    mkdir_if_not_exists(jm_download_dir)

    def decide_filepath(e):
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)

        if resp is None:
            suffix = str(time_stamp())
        else:
            suffix = resp.url

        name = '-'.join(
            fix_windir_name(it)
            for it in [
                e.description,
                current_thread().name,
                suffix
            ]
        )

        path = f'{jm_download_dir}/【出错了】{name}.log'
        return path

    def exception_listener(e: JmcomicException):
        """
        异常监听器，实现了在 GitHub Actions 下，把请求错误的信息下载到文件，方便调试和通知使用者
        """
        # 决定要写入的文件路径
        path = decide_filepath(e)

        # 准备内容
        content = [
            str(type(e)),
            e.msg,
        ]
        for k, v in e.context.items():
            content.append(f'{k}: {v}')

        # resp.text
        resp = e.context.get(ExceptionTool.CONTEXT_KEY_RESP, None)
        if resp:
            content.append(f'响应文本: {resp.text}')

        # 写文件
        write_text(path, '\n'.join(content))

    JmModuleConfig.register_exception_listener(JmcomicException, exception_listener)


if __name__ == '__main__':
    main()
