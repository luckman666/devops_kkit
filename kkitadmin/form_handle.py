from django.forms import ModelForm

# form对应的是每一个数据库表做的校验，而我们生产form表单的时候没办法知道是哪个表要创建form
# 动态创建一个类
def create_dynamic_model_form(admin_class,form_add=False):
    """动态的生成modelform
    form_add: False 默认是修改的表单,True时为添加
    """
    # 类方法，拿到用户选择的模板的所有行数据，并且添加form_add属性判断是编辑模式还是添加模式
    class Meta:
        # 得到需要生成form的模板
        model = admin_class.model
        # fields = ['name','consultant','status']
        # 取出该模板的所有字段
        fields = "__all__"
        # 如果form_add是false即编辑模式
        if not form_add:#change
            # 将admin_class用户设置的只读表排除
            exclude = admin_class.readonly_fields
            admin_class.form_add = False #这是因为自始至终admin_class实例都是同一个,
            # 这里修改属性为True是为了避免上一次添加调用将其改为了True
        else: #add
            admin_class.form_add = True
    # 获得字段对象，并且添加样式
    def __new__(cls, *args, **kwargs):
        # 得到这个form类的所有字段名cls.base_fields
        for field_name in cls.base_fields:
            # 获得字段对象
            filed_obj = cls.base_fields[field_name]
            # 这个是表单的样式class='form-control'，给每个表单添加样式
            filed_obj.widget.attrs.update({'class':'form-control'})

            # if field_name in admin_class.readonly_fields:
            #     filed_obj.widget.attrs.update({'disabled': 'true'})
            #     print("--new meta:",cls.Meta)

        #print(cls.Meta.exclude)
        return  ModelForm.__new__(cls)
    # 使用type创建一个类，类名称，继承父类的集合（元组形式并且可以写多个），方法的名称
    dynamic_form = type("DynamicModelForm" ,(ModelForm,) ,{'Meta' :Meta,'__new__':__new__})

    # print(dynamic_form)
    return dynamic_form