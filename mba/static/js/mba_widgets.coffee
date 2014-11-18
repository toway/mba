$ ()->
    $.widget "mbawidget.metadialog",
        options:
            name: 'metadialog'
            title: null
            desc: null
            content: 'Nothing here!'
            remoteContent: {
                type: null  # json, script, html, etc
                url: null
                rootVar: null # needed for script type, because we need to know which vartibal  to evaluate
            }
            width : null
            buttons: []


        defaultButtons: [
                {
                    name: 'ok'
                    clsNames: 'btn btn-xs btn-primary'
                    value: '保&nbsp;&nbsp;存'
                    handler: 'onOk'
                },{
                    name: 'cancel'
                    clsNames: 'btn btn-xs btn-default'
                    value: '取&nbsp;&nbsp;消'
                    handler: 'onCancel'
                }

            ]

        dialog: null
        visible: false

        _create: ()->

            this._on this.element,
                'click': "toggle"
            this._on this.document,
                'click': "hideDialog"

            return


        _destroy: ()->
            this._off this.element
            this._off this.document
            for index,item in $.dialog.find('button')
                this._off item
            this.dialog.remove()


        onOk: ()->
            console.log 'onOk'
            this.hideDialog()
            return false

        onCancel: ()->
            console.log 'onCancel'
            this.hideDialog()
            return false



        toggle: ()->
            if this.visible
                this.hideDialog()
            else
                this.showDialog()




            return false

        showDialog: ()->
            console.log "showDialog"
            offset = this.element.offset()
            offset.top += this.element.height() + 10
            self = this

            if not this.dialog
                # dialog is not created, craete it now

                if this.options.remoteContent.type is not null
                    # dialog content is remote content, callback

                    this.buildDialog ()->
                        self.dialog.show().offset offset
                        self.visible = true
                        return
                    return

                else
                    this.buildDialog()



            this.dialog.show().offset offset
            this.visible = true

            return


        hideDialog: (e)->
            console.log 'before hideDialog'

            hide = false

            if this.dialog
                if  e
                    if this.dialog.find(e.target).length == 0
                        hide = true
                else
                    hide = true



            if hide
                console.log "hideDialog:"
                this.dialog.hide()
                this.visible = false

            return


        buildTitle: ()->
            desc = ""
            desc = "<small>(" + this.options.desc + ")</small>"  if this.options.desc

            title = $ "<div/>"
                .addClass "mba-dialog-title"
                .html(this.options.title + desc)

            return title.prop('outerHTML')

        hookRemoteContent: (content)->
            '''After got remote content, hook it to the dialog content area or other items'''
            this.dialog.find('.mba-dialog-content').html(content)
            return false

        buildContent: ()->
            remoteContent = this.options.remoteContent
            self = this

            content = $("<div/>")
                        .addClass "mba-dialog-content"

            if remoteContent.type == 'json'
                $.get remoteContent.url,
                    (ret)->
                        if ret.errcode == ret.SUCCESS
                            retdata = ret.retval
                            rootVar = self.options.remoteContent.rootVar
                            retdata = ret.retval[rootVar] if rootVar
                            self.hookRemoteContent retdata
                        else
                            alert ret.errmsg
                        return

            else if remoteContent.type == 'script'
                $.getScript remoteContent.url,
                    (ret)->
                        eval ret
                        obj = window[remoteContent.rootVar]
                        self.hookRemoteContent obj
                        return

            else if remoteContent.type is null
                # data is local parameter,  return the content directly
                content.html this.options.content
            else
                alert "Not supported remoteContent type"

            content.html ' Loading... '
            return content.prop("outerHTML")

        buildFooter: ()->
            buttons = this.options.buttons
            defaultButtons = this.defaultButtons
#            newButtons = defaultButtons + []

            for i, idx in buttons
                found = false
                for j in defaultButtons
                    if i.name == j.name

                        defaultButtons[idx] =   $.extend( j, i )
                        found = true
                        break

                defaultButtons.append i if not found

            this.options.buttons = defaultButtons

            arr = []

            for item ,index in defaultButtons
                button = $("<button/>")
                            .addClass item.clsNames
                            .attr "name", item.name
                            .val item.name
                            .html item.value
                            .attr "type", "button"
                btnhtml = button.prop('outerHTML')
                arr.push(btnhtml)

            footer = $ "<div/>"
                .addClass "mba-dialog-footer"
                .append arr.join("&nbsp;&nbsp;&nbsp;")

            return footer.prop('outerHTML')

        buildDialog: (cb)->
            title = this.buildTitle()
            content = this.buildContent()
            footer = this.buildFooter()

            this.dialog = $ "<div/>"
                    .addClass "mba-dialog"
                    .append( title + content + footer)
                    .appendTo( this.document.find "body")


            if this.options.width
                this.dialog.css("width", this.options.width)

            for item,index  in  this.dialog.find("button")
                this._on item,
                    'click': this.options.buttons[index].handler



            this.postBuildDialog()

            cb() if cb

            return false

        postBuildDialog: ()->
            return false


    return


## Abstract widget of all structed data dialog
$ ()->
    $.widget "mbawidget.structdata",
        $.mbawidget.metadialog,
        options:
            name: 'structdata'
            items: null



        buildStructContent:()->
            return  ",".join(this.options.items)



        buildContent: ()->
            if this.options.remoteContent.type is null
                div = $ "<div>"
                    .addClass "mba-dialog-content"
                    .append( this.buildStructContent()  )
                return div.prop("outerHTML")

            return  this._super()


        hookRemoteContent: (content)->
            this.options.items = content
            content2 = this.buildStructContent()
            this.dialog.find('.mba-dialog-content').html content2


$ ()->
    $.widget "mbawidget.plain",
        $.mbawidget.structdata,
        options:
            name: 'plain2'
            items: null
            columns: 2


        buildCell: (row, col, item)->
            return item

        buildStructContent:()->
            table = ""

            cols = this.options.columns
            len = this.options.items.length
            rows = (len-1) / cols + 1

            for row in [0..rows-1]
                tr = ""
                for col in [0..cols-1]
                    if row*cols+col < len
                        item = this.options.items[row*cols+col]
                        td = "<td class='mba-dialog-item'>"+this.buildCell(row, col, item)+"</td>"
                    else
                        td = "<td class='mba-dialog-item'></td>"
                        break


                    tr += td

                tr = "<tr>" + tr + "</tr>"
                table += tr

            table = "<form><table>" + table + "</table></form>"
            return table


$ ()->
    $.widget "mbawidget.radiocheck",
        $.mbawidget.plain,
        options:
            name: 'radiocheck'


        onOk: ()->
            val = this.dialog.find(":radio:checked").val()
            this.element.val val
            return this._super()


        buildCell: (row, col, item)->
            name = this.options.name
            id = this.options.title+name+item
            td = "<input type='radio' id='"+id+"' name='"+name+"' value='"+item+"'/>"
            td += "<label for='"+id+"'>"+item+"</label>"
            return td


$ ()->
    $.widget "mbawidget.multicheck",
        $.mbawidget.plain,
        options:
            name: 'multicheck'
            maxcount: 3


        onOk: ()->
            checked = this.dialog.find ":checkbox:checked"

            val = ( $(item).val() for item in checked).slice(0,  this.options.maxcount)

            this.element.val val.join(",")
            return this._super()

        buildCell: (row, col, item)->
            name = this.options.name
            id = this.options.title+name+item
            td = "<input type='checkbox'  id='"+id+"' name='"+name+"' value='"+item+"'/>"
            td += "<label for='"+id+"'>"+item+"</label>"
            return td




$ ()->
    $.widget "mbawidget.tree",
        $.mbawidget.structdata,
        options:
            name: 'tree'
            maxtreelevel: 2 # 树的层级,  目前最大支持2层, 以后可能 支持三层


        buildStructContent: ()->

            content = ""
            items = this.options.items
            for item,index in items
                item =  "<a href='javascript:void(0)' data-index="+index+" class='mba-dt-l1'>" + item.name + "</a>|"
                content += item

#            for i in [0..maxtreelevel-1]
#
#                content += "<hr/><div  class='mba-dt-l"+dataidx+"'</div>"


            content += "<hr/><div class='mba-dt-l2'></div>"

            return content



        postBuildDialog: ()->

            this._on this.dialog,
                'click a': '_buildL2'

            return false

        buildCell: (row, col, item)->
            return item

        _buildL2: (e)->
            idx = parseInt $(e.target).attr("data-index")
            subitems = this.options.items[idx].items

            table = ""
            cols = 3
            len = subitems.length
            rows = (len-1) / cols + 1

            for row in [0..rows-1]
                tr = ""
                for col in [0..cols-1]
                    if row*cols+col < len
                        item = subitems[row*cols+col].name
                        td = "<td class='mba-di-l2'>"+this.buildCell(row, col, item)+"</td>"
                    else
                        td = "<td class='mba-di-l2'></td>"
                        break

                    tr += td

                tr = "<tr>" + tr + "</tr>"
                table += tr

#            table = "<form><table>" + table + "</table></form>"

            subnodes = this.dialog.find '.mba-dt-l2'

            table = "<table id='subidx-"+idx+"'>" + table + "</table>"
            section = subnodes.find('table[id=subidx-'+idx+']')

            subnodes.find("table[id^=subidx]").hide()

            if section.length == 0 #can't find it
                subnodes.append table
            else:
                section.show()

            return
#            this.dialog.find('.mba-dt-l2').html table


    return

$ ()->
    $.widget "mbawidget.radiotree",
        $.mbawidget.tree,
        options:
            name: 'radiotree'



        onOk: ()->
            val = this.dialog.find(":radio:checked").val()
            this.element.val val
            return this._super()


        buildCell: (row, col, item)->
            name = this.options.name
            id = this.options.title+name+item
            td = "<input type='radio' id='"+id+"' name='"+name+"' value='"+item+"'/>"
            td += "<label for='"+id+"'>"+item+"</label>"
            return td

$ ()->
    $.widget "mbawidget.multichecktree",
        $.mbawidget.tree,
        options:
            name: 'multichecktree'
            maxcheckNumAllow: 3

        onOk: ()->
            checked = this.dialog.find ":checkbox:checked"

            val = ( $(item).val() for item in checked).slice(0,  this.options.maxcheckNumAllow)

            this.element.val val.join(",")
            return this._super()

        buildCell: (row, col, item)->
            name = this.options.name
            id = this.options.title+name+item
            td = "<input type='checkbox'  id='"+id+"' name='"+name+"' value='"+item+"'/>"
            td += "<label for='"+id+"'>"+item+"</label>"
            return td








## Abstract widget of all input data dialog
$ ()->
    $.widget "mbawidget.textareadialog",
        $.mbawidget.metadialog,
        options:
            name: 'textareadialog'
            rows: 3
            width: 200


        buildContent: ()->
            content = $("<div/>")
                        .addClass "mba-dialog-content"

            textarea = "<textarea type='input' class='form-control' rows="+this.options.rows+"></textarea>"
            return (content.html textarea).prop("outerHTML")


