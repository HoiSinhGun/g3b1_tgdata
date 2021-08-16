ELE_TYP_lc = dict(id='LC', colname='lc', type='str', length='2')
ELE_TYP_lc2 = dict(id='LC2', colname='lc_2', type='str', length='2')
ELE_TYP_chat_id = dict(id='chat_id', colname='tg_chat_id', type='int')
ELE_TYP_cmd = dict(id='cmd', colname='cmd', type='str', length='13')
ELE_TYP_send_onyms = dict(id='send_onyms', colname='send_onyms', type='bool')
ELE_TYP_txt_seq_id = dict(id='txt_seq_id', colname='txt_seq_id', type='int')
ELE_TYP_tst_template_id = dict(id='tst_template_id', colname='tst_template_id', type='int')
ELE_TYP_tst_template_it_id = dict(id='tst_template_it_id', colname='tst_template_it_id', type='int')
ELE_TYP_tst_mode = dict(id='tst_mode', colname='tst_mode', type='int',
                        allow_val=[dict(id=1, bkey='tst_mode_edit'), dict(id=2, bkey='tst_mode_execute')])


