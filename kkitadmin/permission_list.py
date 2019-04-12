from kkitadmin import custom_perm_logic

perm_dic= {
    # table_obj_list是urlname值，后面跟的动作，
    # permission_hook.view_my_own_customers自定义用户可以使用的权限，写出函数可以返回ture或者False结果就可以permission_hook有示例
    #'crm_table_index': ['table_index', 'GET', [], {'source':'qq'}, ],  # 可以查看CRM APP里所有数据库表
    # 'SalesCrm_table_list': ['table_obj_list', 'GET', [], {},permission_hook.view_my_own_customers],  # 可以查看每张表里所有的数据
    'crm_table_index':['table_index','GET',[],{},],
    'crm_table_list':['table_list','GET',[],{}],
    'crm_table_list_action':['table_list','POST',[],{}],
    'crm_table_list_view':['table_change','GET',[],{}],
    'crm_table_list_change':['table_change','POST',[],{}],
    'crm_can_access_my_clients':['table_list','GET',[],
                                 {'perm_check':33,'arg2':'test'},
                                 custom_perm_logic.only_view_own_customers],

}



