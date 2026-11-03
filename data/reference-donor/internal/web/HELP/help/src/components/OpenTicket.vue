<template>
    <div id="content">
        <div id="problemContent">
            <div class="item">
                <label>Type of problem</label>
                <select v-model="params.problemType" class="input">
                    <option value="">Choose problem</option>
                    <option v-for="problem in problems" :value="problem.key">{{problem.value}}</option>
                </select>
            </div>
            <div class="item">
                <label>Your license</label>
                <input disabled v-model="params.license" class="input" type="text">
            </div>
            <div class="item">
                <div>
                    <label>Your email</label>
                    <input v-model="params.email" class="input" type="text">
                </div>
            </div>
        </div>
        <div id="descriptionContent">
            <label>Description</label>
            <textarea v-model="params.description"></textarea>
        </div>
        <div id="attachmentContent">
            <div id="attachLabel">
                <label>Attach project config(s), logs, strategies, screenshots, other files:</label> 
                <span @click="showModal = true" id="addFile">Add file</span>
                <span id="attachmentSize">Total attachments size: {{getTotalSize()}}</span>
            </div>
            <div id="attachments">
                <div v-for="(attachment, index) in params.attachments" :key="index" class="attachment">{{attachment.name}} <span class="size">{{displaySize(attachment.size)}}<span @click="removeAttachment(index)" class="remove">X</span></span></div>
            </div>
        </div>
        <div id="buttonContent">
            <button @click="submitSupportTicket">Submit support ticket</button>
        </div>
    </div>
    <div id="backToHelpContent">
        <span @click="changePage('qna')">&lt;&nbsp;&nbsp;Back to Help</span>
    </div>
    <Teleport to="body">
        <AddFile @updateData="updateData" :data="data" @selectStrategiesClicked="selectStrategiesClicked()" :show="showModal" @close="showModal = false">
            <template #header>
                <h3>custom header</h3>
            </template>
        </AddFile>
        <SelectStrategies @updateData="updateData" :data="data" :show="showSelectStrategies" @close="showSelectStrategies = false">
        </SelectStrategies>
    </Teleport>
</template>

<script>
import axios from 'axios'
import AddFile from './AddFile.vue'
import SelectStrategies from './SelectStrategies.vue'

export default {
  name: 'OpenTicket',
  props: {
  },
  components: {
    AddFile,
    SelectStrategies
  },
  methods:{
    selectStrategiesClicked(){
        showSelectStrategies = true
    }
    changePage(page){
      this.$emit('changePage', page)
    },
    removeAttachment(index){
        this.params.attachments.splice(index, 1)
    },
    async submitSupportTicket(){
        let result = await axios({
            method: 'post',
            url: '/help/submitSupportTicket',
            data: {
                problemType: this.params.problemType,
                license: this.params.license,
                email: this.params.email,
                attachments: this.attachments
            }
        });
        return result.data;
    },
    addFile(){
        this.changePage('addFile')
    },
    async loadSupportTicketInfo(){
        let result = await axios({
            method: 'post',
            url: '/help/loadSupportTicketInfo'
        });
        return result.data;
    },
    getTotalSize(){
        let sum = 0;
        for(let attachment of this.params.attachments){
            sum += parseInt(attachment.size);
        }
        return this.displaySize(sum)
    },
    displaySize(size){
        return size + " KB"
    },
    updateData(data){
        this.data = data;
    }
  },
  data () {
    return {
      params: {
        attachments: [
            {name: "testing 1", size: "323", "data": {}},
            {name: "testing 2", size: "323", "data": {}},
            {name: "testing 3", size: "323", "data": {}},
            {name: "testing 4", size: "323", "data": {}},
            {name: "testing 5", size: "323", "data": {}},
            {name: "testing 6", size: "323", "data": {}}
        ],
        problemType: "",
        license: "",
        email: ""
      },
      showModal: false,
      showSelectStrategies: false,
      problems: [
        {"key": "General question", "value": "General question"},
        {"key": "Error during build", "value": "Error during build"},
        {"key": "Custom project issue", "value": "Custom project issue"},
        {"key": "Suggestion", "value": "Suggestion"},
        {"key": "Bug report", "value": "Bug report"},
        {"key": "Licensing issue", "value": "Licensing issue"}
      ],
      data: {
        addFileParams: {
            type: "strategyFromDatabank",
            project: "",
            databank: "",
            strategies: "",
            projectConfigs: [],
            programLogs: [],
            file: "",
            selectedFile: {}
        }
      }
    }
  },
  async mounted(){
    let supportTicketInfo = await this.loadSupportTicketInfo();
    this.params.license = supportTicketInfo.license;
  }
}
</script>

<style scoped>
    #content{
        background-color: rgb(236, 236, 236);
        padding: 15px 30px 15px 30px;
    }

    #problemContent{
        display: grid;
        grid-template-columns: 33% 33% 33%;
        grid-template-rows: auto auto;
    }

    #problemContent label{
        display: block;
    }
    #problemContent .input{
        border-radius: 3px;
        width: 100%;
        padding: 5px 0px 5px 9px;
        border: 1px solid rgb(200, 200, 200);
    }
    #problemContent .input:focus{
        border: 1px solid rgb(50, 50, 50);
        outline: none !important;
    }
    #problemContent .item{
        margin-right: 15px;
    }
    textarea{
        border: 1px solid rgb(200, 200, 200);
    }
    textarea:focus{
        border: 1px solid rgb(50, 50, 50);
        outline: none !important;
    }

    #descriptionContent{
        margin-top: 15px;
    }
    #descriptionContent label{
        display: block;
    }
    #descriptionContent textarea{
        width: 100%;
        height: 35vh;
    }

    #attachmentContent{
        margin-top: 15px;
    }

    #attachmentContent #attachLabel{
        font-size: min(12px, 1.5vw)
    }

    #addFile{
        color: blue;
        text-decoration: underline;
        margin-left: 0.5vw;
        cursor: pointer;
    }
    #attachmentSize{
        float: right;
    }
    #attachments{
        margin-top: 15px;
        display: grid;
        grid-template-columns: 50% 50%;
        max-height: 35vh;
        justify-content: start;
    }
    #attachments .attachment{
        border: 1px solid grey;
        padding: 3px 6px 3px 6px;
        margin: 5px;
        border-radius: 3px;
    }
    #attachments .attachment .size{
        float: right;
        color: blue;
    }
    #attachments .attachment .remove{
        background-color: grey;
        padding: 1px 5px 1px 5px;
        float: right;
        color: blue;
        margin-left: 5px;
        cursor: pointer;
        color: rgb(236, 236, 236);
        border-radius: 3px;
    }
    #buttonContent{
        margin-top: 15px;
        display: flex;
        justify-content: center;
    }
    #buttonContent button{
        background: rgb(0, 158, 231);
        padding: 6px 15px 6px 15px;
        color: white;
        border: none;
        margin-left: 15px;
        cursor: pointer;
    }

    #backToHelpContent{
        margin-top: 15px;
    }
    #backToHelpContent span{
        cursor: pointer;
        font-weight: 700;
    }
</style>
