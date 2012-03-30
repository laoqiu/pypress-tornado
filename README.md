Pypress, 由python编写的团队博客
===========================

### 最近改动
* 2012-3-24: 加入第二套皮肤 simple
* 2012-3-25: 完善侧栏最后评论功能
* 2012-3-26: 完善友情链接模块功能
* 2012-3-30: 加入session机制
    * 支持redis存储或使用tornado的secure_cookie
    * 使用不用方法时，只需要设置settings的REDIS_SERVER开关  
    * 支持session有效期的设置，可使用PERMANENT_SESSION_LIFETIME


### 项目介绍

原先版本基于flask框架

flask是一个很不错的框架，写项目比较轻松，较多高质量的插件，帮助python新手能快速创建自己的项目。
而且也有不少国外项目可以参考，比如newsmeme，原先的pypress就是学习的这个项目而创建的，非常受用。

pypress原也是自己的学习项目，没想到还有许多朋友来邮件表示在用，原想在flask上继续更新，但又学习上了tornado，于是直接使用tornado重写了。

说下tornado，是一个不错的server，但做框架，还是缺少太多东西，写了一段时间tornado，我已经开始怀念flask的高效了....

反正是学习，我将flask自己比较中意的插件，应用在了tornado上，并做了相应修改：

1.  sqlalchemy
    改动最大，比如分页类(Pagination)，以及_SinalTrackingMapperExtension类_record输入处理等

2.  wtforms  
    只是简单的对tornado的request进行了处理

3.  cache
    这是从werkzeug源码里copy的类进行了修改

4.  signals
    这是纯从flask里拿来的，只是对blinker的导入进行了简单处理而已

5.  routing
    这是为tornado的反向路由写的一个比较简单的类，解决了tornado只在handler里使用reverse_url的问题

6.  permission
    这个也是纯从flask里拿来的，只是做了一点点小改动，让它能在tornado里使用


而pypress-tornado，目前没有原先pypress功能丰富，主要改动:

1.  换了个编辑器，从国外一个简单的demo基础上改进而来，也许会有一些bug :(

2.  加了评论验证码

3.  去除了twitter相关内容

项目演示: [laoqiu.com](http://laoqiu.com/ "laoqiu blog")


