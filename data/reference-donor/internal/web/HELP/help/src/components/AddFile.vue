<script>
import axios from 'axios'
export default {
  props: {
    show: Boolean,
    data: {}
  },
  data(){
    return {
      selectedFile: "",
      projects: [],
      databanks: []
    }
  },
  methods:{
    async loadProjects(){
        let result = await axios({
            method: 'post',
            url: '/help/loadProjects'
        });
        return result.data;
    },
    async loadStrategies(projectName, databankName){
        let result = await axios({
            method: 'post',
            url: '/help/loadStrategies?projectName=' + projectName + "&databankName=" + databankName
        });
        return result.data;
    },
    async loadDatabanks(projectName){
        let result = await axios({
            method: 'post',
            url: '/help/loadDatabanks?projectName=' + projectName
        });
        return result.data;
    },
    async projectChanged(){
        let result = await this.loadDatabanks(this.data.addFileParams.project);
        let databanks = []
        for(let databank of result.databanks){
            databanks.push({
                key: databank.name,
                value: databank.name
            })
        }
        this.databanks = databanks;
    },
    async browse(){
      if(this.data.addFileParams.type == 'fileOnDisk'){
        let result = await axios({
            method: 'post',
            url: '/help/chooseFiles'
        });
        result = result.data;
        let data = this.data;
        data.addFileParams.selectedFile = result.file;
        this.$emit('updateData', data)
      }
    }
  },
  async mounted(){
    let result = await this.loadProjects();
    let projects = []
    for(let project of result.projects){
        projects.push({
            key: project.projectName,
            value: project.projectName
        })
    }
    this.projects = projects;
  }
}
</script>

<template>
  <Transition name="modal">
    <div v-if="show" class="modal-mask">
      <div class="content">
        <div id="strategyFromDatabank" class="selection">
          <div><input v-model="data.addFileParams.type" value="strategyFromDatabank" type="radio">Strategy from databank</div>
          <div class="data">
              <select @change="projectChanged()" :disabled="data.addFileParams.type != 'strategyFromDatabank'" v-model="data.addFileParams.project">
                  <option value="">Choose project</option>
                  <option v-for="project in projects" :value="project.key">{{project.value}}</option>
              </select>
              <select :disabled="data.addFileParams.type != 'strategyFromDatabank' || data.addFileParams.project == ''" v-model="data.addFileParams.databank">
                  <option value="">Choose databank</option>
                  <option v-for="databank in databanks" :value="databank.key">{{databank.value}}</option>
              </select>
              <div @click="$emit('selectStrategiesClicked')" id="chooseStrategies">
                Choose strategies
              </div>
          </div>
        </div>
        <div id="fileOnDisk" class="selection">
          <div><input v-model="data.addFileParams.type" value="fileOnDisk" type="radio"> File on disk</div>
          <div class="data">
              <span @click="browse()" class="browse">Browse</span>
              <div class="file">
                {{data.addFileParams.selectedFile.name}}
              </div>
          </div>
        </div>
        <div align="right" id="buttons" class="selection">
          <span @click="$emit('close')" class="close">Close</span>
          <button @click="save()" class="save">Save</button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style>
  .modal-mask {
    position: fixed;
    z-index: 9998;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content:center;
    transition: opacity 0.3s ease;
  }
  .content{
    background: white;
    padding: 30px;
    width: auto;
    transition: all 0.3s ease;
  }
  .selection{
      margin-bottom: 15px;
  }
  #chooseStrategies{
    border: 1px solid grey;
    align-items: center;
    justify-content: center;
    display: flex;
    border-radius: 3px;
    cursor: pointer;
  }
  #strategyFromDatabank .data{
      margin-top: 15px;
      display: grid;
      grid-template-columns: 33% 33% 33%;
  }
  #strategyFromDatabank .data select{
      margin-right: 15px;
      padding: 6px 15px 6px 6px;
  }
  .selectionTable .data{
      margin-top: 15px;
      max-height: 25vh;
  }
  .selectionTable .table{
      display: inline-block;
      border-collapse: collapse;
  }
  .selectionTable .table tr,td{
      border: 1px solid grey;
      border-collapse: collapse;
  }
  .selectionTable .table .text{
      padding: 3px 90px 3px 9px;
  }
  #fileOnDisk .data{
      margin-top: 15px;
  }
  #fileOnDisk .browse{
      color: blue;
      cursor: pointer;
  }
  #buttons{
      border-top: 1px solid grey;
      padding-top: 15px;
  }
  #buttons .close{
      cursor: pointer
  }
  #buttons .save{
      background: rgb(0, 158, 231);
      padding: 6px 15px 6px 15px;
      color: white;
      border: none;
      margin-left: 9px;
      cursor: pointer;
  }

  .modal-enter-from {
    opacity: 0;
  }

  .modal-leave-to {
    opacity: 0;
  }

  .modal-enter-from .content,
  .modal-leave-to .content {
    -webkit-transform: scale(1.1);
    transform: scale(1.1);
  }

  .file{
    margin-top: 10px;
  }
</style>