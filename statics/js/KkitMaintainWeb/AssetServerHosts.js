//判断是否有点击编辑模式的函数
$(function () {
    bindEditMode();
    bindCheckbox();
    bindSave();
    bindAccReditLogin();
    // bindAccReditLoginAction();
});

//ip地址正则表达式
function isValidIP(ip) {
    var reg = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/
    return reg.test(ip);
}
//端口正则验证
function isValidProt(prot) {
    var reg = /^([0-9]|[1-9]\d{1,3}|[1-5]\d{4}|6[0-5]{2}[0-3][0-5])$/
    return reg.test(prot);
}
//编辑按钮
function bindEditMode() {
//            先找到id值为idEditMpode按钮，绑定点击事件click，jquery里面事件都没有on
            $('#idEditMpode').click(function () {
//                引用对象本身,检查按钮对象是否有btn-warning的属性
                var editing = $(this).hasClass('ellipse-red');

//                如果有btn-warning属性说明该属性已经点击了。那么执行退出编辑。移除属性
            if (editing) {
                $(this).removeClass('ellipse-red');
                $(this).addClass('ellipse-blue');
                $(this).text('进入编辑模式');

//                    定位#table_tb id的位置，从这个id往下找find，所有type=checked的标签。对其进行遍历
                var $currentTr = $("tr[class='CheckAll active']")
//                        带入到该编辑函数中
                trOutEditMode($currentTr);
            } else {
//如果没有这个属性就是没被点击过，所以是进入编辑模式
                $(this).removeClass('ellipse-blue');
                $(this).addClass('ellipse-red');
                $(this).text('退出编辑模式');

                // 遍历出所有的TR标签，用户选中的
                var $currentTr = $("tr[class='CheckAll active']");
                trIntoEditMode($currentTr);
            }
        })
            }

//        判断勾选框编辑函数
function bindCheckbox(thi) {
                //编辑按钮是否已经按下了
                if ($('#idEditMpode').hasClass('ellipse-red')) {
                        //用户选中的是否已经勾选
                        var act = $(thi).hasClass('active')
                    if (act){
                        //    勾选去in,否则去out
                        trIntoEditMode(thi);
                    } else {
                        console.log("退出编辑模式")
                        trOutEditMode(thi);
                    }
                }

        }
//进入编辑模式
function trIntoEditMode($Tr){

    $Tr.children().each(function () {
//      $(this)表示所有被遍历出来的纸标签，然后.attr查看是否有该属性。返回true或者fals
//                console.log($tr)                 $(this).attr('new-val',inputValue);
        $(this).parent().attr('has-edit',true);
        // console.log('aaaaa',$(this))
        var editEnable = $(this).attr('edit-enable');
//                取出传递过来的编辑类型变量
        var editType = $(this).attr('edit-type');

//                如果这个标签属性为true
        if(editEnable=='true'){
//                    如果编辑类型是select下拉框
//                    下拉框样式：
//                    <select value="默认值(1)">
//                           <option value="1">上线</option>
//                            <option value="2">下线</option>
//                             <option value="3">上架</option>
//                    <select>
            if (editType == "select"){
//                        那么取出其变量名
                var globalName = $(this).attr('global-name')
//                        取出其默认值
                var origin = $(this).attr('origin')
//                        设置下来狂元素
                var sel = document.createElement('select')
//                        设置classname的样式名
                sel.className ='form-control';
//                        遍历全局变量中的列表内容
                $.each(window[globalName],function (k1,v1) {
//                            每遍历一次创建option属性
                    var op = document.createElement('option')
//                            设置<option value="值">值在全局变量列表的0号位
                    op.setAttribute('value',v1[0]);
//                            console.log(v1[1])
//                            添加<option value="值">文本信息</option>
                    op.innerHTML=v1[1];
//                            将整个op添加到select标签中
                    $(sel).append(op)
                })
//                        jquery方式给select标签添加默认值
                $(sel).val(origin)
//                        用jquer方式将select添加到页面中
                $(this).html(sel);

            }else if (editType == "input"){
            var innerText = $(this).text();
//                    创建一个input标签
                console.log('innerText!!!!!!!',innerText)
            var tag = document.createElement('input');
//                    设置input标签的样式名
            tag.className ='form-control'
//                    input标签value属性的值是innerText，也就是将原有标签内容再填入到input中
            tag.value = innerText;
//                    将tag填入html中，html可以将文本以属性的方式填到页面中。
            $(this).html(tag);
            }
//                    那么取出他的文本信息
        }
    })
}
//        退出编辑模式后恢复文本信息
function trOutEditMode($tr) {
//遍历tr子目录的td属性

    $tr.children().each(function () {
//                查看属性是否有edit-enable
    var editEnable = $(this).attr('edit-enable');
    var editType = $(this).attr('edit-type');
    if (editEnable == 'true') {
        if (editType == 'select'){
//                    var globalName = $(this).attr('global-name')
//                    查找到下拉框呗选中的值
            var newText = $(this).find("option:selected").text()
            var newId = $(this).find("option:selected").val()
//另一种取值的方法
//                    var $select = $(this).children().first()
//                    var newId = $select .val()
//                    var newText = $select[0].selectedOptions[0].innerHTML;
//                    console.log(sel_text)

//                    console.log(sel_val)
            $(this).html(newText);
//                    每次更改都新加一个属性来存储改变的键值，以后保存的时候过来取
            $(this).attr('new-val',newId)
        }else if (editType == 'input'){

           var $input = $(this).children().first();
           //                    取出值,去掉两边的空格
           var inputValue = $.trim($input.val());
           //                    再把值写入
            $(this).attr('new-val',inputValue);
           $(this).html(inputValue);
           // $(this).attr('new_val',inputValue);
        }

        }
    })
    }

//数组去重
function unique(arr){
  var hash=[];
  for (var i = 0; i < arr.length; i++) {
    for (var j = i+1; j < arr.length; j++) {
      if(arr[i]===arr[j]){
        ++i;
      }
    }
      hash.push(arr[i]);
  }
  return hash;
}

//        保存
function bindSave() {
   $('#Save').click(function (){
      var postList = []
       $('#table_tb').find('tr[has-edit="true"]').each(function () {
           var HsotId = $(this).children().children().attr('id');
           var temp = {};
           var  host= {};
           host['id'] = HsotId;
           // temp['id'] =HsotId;
           $(this).children('[edit-enable="true"]').each(function () {
               var origin= $(this).attr('origin');
               var newVal = $(this).attr('new-val');
               var name = $(this).attr('name');
               if (name === 'ip_addr'){
                   if(isValidIP(newVal)){
                      if (origin != newVal) {
                           temp[name] = newVal;
                        } else {
                       }
                   } else {
                       alert(newVal + ' IP地址格式书写不规范')
                       return false;
                   }
               }
               if (name === 'port'){
                   if(isValidProt(newVal)){
                      if (origin != newVal) {
                           temp[name] = newVal;
                        } else {
                       }
                   } else {
                       alert(newVal + ' 端口格式书写不规范')
                       return false;
                   }
               }

              if (origin != newVal) {
                   temp[name] = newVal;
                } else {
               }
           })
           host['data']=temp
           postList.push(host)
            console.log('postList',postList)
   });






//       获取token值
    var csrftoken = Cookies.get('csrftoken');
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    $.ajaxSetup({
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    // console.log(csrftoken);

       // var jsonData = JSON.stringify(post_list);
//                 console.log(jsonData)
//               提交数据
       $.ajax({
            url:'/api/hostschange/',
            type: 'POST',
            data: {'post_list': JSON.stringify(postList)},
            // headers: {'Content-Type': 'application/json',"X-CSRFToken":csrftoken},
            dataType: 'JSON',
            success:function (result) {
                if(result.status === 4103){
                    alert(result.message)
                } else {
                    console.log(result.status)
                    // FlushWindos()
                }
            }
        })


   })
}
//授权登录按钮,初始检查及弹出模态框
function bindAccReditLogin(btn_val) {
//            先找到id值为idEditMpode按钮，绑定点击事件click，jquery里面事件都没有on

   if (btn_val === '登录授权控制台') {
            postDic = {
                //选择了几个服务器
                'selected_hosts': [],
                "selected_hosts_ip_addr":[],
                'TokenExpireTime': [],
                'UserIdList': [],
                'token_type': 'host_token'
            };
            var err_msg = [];
            //run form submistion check before submit
            var selected_hosts = $("tr[id='TableRow']").filter(".active");
            if (selected_hosts.length == 0) {
                err_msg.push("未选中任何主机执行任务！");
                //            show_alert(err_msg);#}
                alert("未选中任何主机执行任务！");
                return false
            }
            //     遍历selected_hosts列表中的内容   #}
            $(selected_hosts).children().children('input').each(function () {
                //      添加主机id 类似host_1  #}
                postDic["selected_hosts"].push($(this).attr("id"));
            });

            $(selected_hosts).find("td[name='ip_addr']").each(function () {
                postDic["selected_hosts_ip_addr"].push($(this).html());
            });
            postDic["selected_hosts"] = JSON.stringify(postDic["selected_hosts"]);
            var DisplayIps = [];
            if (err_msg.length === 0) { // passed form submition check
                $(selected_hosts).find("td[name='ip_addr']").each(function () {
                    DisplayIps.push(" <br> <i class='fa fa-laptop' aria-hidden='true'></i>  IP为： "+$(this).html()+" </br> ")
                });
                UniqueHostsNameList = unique(DisplayIps);
                //登录授权模态框显示
                $("#HostD").html(UniqueHostsNameList);
                //    显示模态对话框        #}
                $('#AccReditLoginModal').modal('show');
                $(this).html("停止批量任务");
                //     拿到用户输入的命令，并且去除两边的空格
            } else {
                $(this).html("登录授权控制台");
            }
        }
    else {
        }
            }
//  确认授权执行js
function bindAccReditLoginAction(ele,post_url) {
    var UserList = [];
    //获取超时时间
    var TokenExpireTime = $('#AccReditLoginModal').find("#TokenExpireTime").val();
    $("#CheckUserParend").children().children('input[type="checkbox"]').each(function () {
        if ($(this).prop('checked')) {
            UserList.push($(this).attr('UserId'))
        }
    });
    if (UserList.length === 0) {
        alert("未选中任何要授予的人！请重新选择");
        condition = false
    } else {

        $("#AccReditLoginModal").modal('hide');
        postDic['TokenExpireTime'] = TokenExpireTime;
        postDic['UserIdList'] = JSON.stringify(UserList);
        $.post(post_url, postDic, function (callback) {
            callbackfuc(callback)
        })
    }
}
