<template>
    <div id="qnaSearch">
        <input v-model="params.searchText" type="text"/>
        <button @click="search()">Search</button>
    </div>
    <div id="qnaResults">
        <div id="topics">
            <div @click="selectTopic(topic.ID)" v-for="topic in topics" class="topic" :class="{ selected: topic.ID == selectedTopicID }" :key="topic.ID">{{topic.name}}</div>
            <div class="topic" :class="{ selected: 'search'== selectedTopicID }" @click="selectTopic('search')" :key="search">Search</div>
        </div>
        <div id="qnaContent">
            <div v-if="qnas.length == 0 && selectedTopicID != 'search'" align="center">
                There is no question and answers in this section.
            </div>
            <div v-if="selectedTopicID == 'search'" align="center">
                <div v-if="qnas.length == 0 && params.searchText">
                    There is no question and answers in this section.
                </div>
                <div v-if="qnas.length == 0 && !params.searchText">
                    Please type in the word you want to search at above and click search.
                </div>
            </div>
            <div @click="selectQna(qna.ID)" v-for="qna in qnas" :key="qna.ID" :class="{selected: qna.ID == selectedQnaID }" class="qna">
                <div class="question">{{qna.question}}</div>
                <div class="answer" v-html="qna.answer"></div>
            </div>
        </div>
    </div>
    <div id="openSupportTicket">
        Haven't found an answer? Do you need to report bug? <button @click="changePage('openTicket')">Open support ticket</button>
    </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'QNA',
  props: {
  },
  methods:{
    changePage(page){
      this.$emit('changePage', page)
    },
    async selectTopic(id){
        this.selectedTopicID = id
        let result = {answers:[]}
        if(id != 'search'){
            result = await this.loadAnswers(this.selectedTopicID);
        } else {
            result = await this.searchAnswers(this.params.searchText);
        }
        this.qnas = result.answers
        if(this.qnas.length > 0){
            this.selectedQnaID = this.qnas[0].ID
        }
    },
    selectQna(id){
        this.selectedQnaID = id
    },
    async search(){
        this.selectedTopicID = "search"
        let result = await this.searchAnswers(this.params.searchText);
        this.qnas = result.answers
        if(this.qnas.length > 0){
            this.selectedQnaID = this.qnas[0].ID
        }
    },
    async loadTopics(){
        let result = await axios({
            method: 'post',
            url: '/help/loadTopics',
            data: {
            }
        });
        return result.data;
    },
    async loadAnswers(id){
        let result = await axios({
            method: 'post',
            url: '/help/loadAnswers?topic_id=' + id,
            data: {
                topic_id: id
            }
        });
        return result.data;
    },
    async searchAnswers(searchText){
        let result = await axios({
            method: 'post',
            url: '/help/searchAnswers?searchText=' + searchText
        });
        return result.data;
    }
  },
  data () {
    return {
      params: {
        searchText: ""
      },
      topics: [],
      qnas: [],
      selectedTopicID: 1,
      selectedQnaID: 1,
      searched: true
    }
  },
  async mounted(){
    let result = await this.loadTopics();
    this.selectedTopicID = result.selectedTopicID
    this.topics = result.topics;
    if(result.answers.length > 0){
        this.selectedQnaID = result.answers[0].ID
        this.qnas = result.answers;
    }
  }
}
</script>

<style scoped>
#qnaSearch{
    width: 100%;
    display: grid;
    grid-template-columns: 85% 10%;
    background-color: rgb(236, 236, 236);
    padding: 3px 0px 3px 0px;
    justify-content: center;
    min-height: 5vh;
}
#qnaResults{
    width: 100%;
    display: grid;
    grid-template-columns: 25% 75%;
    margin-top: 15px;
    height: 80vh;
}
#topics{
}
#qnaContent{
    background-color: rgb(236, 236, 236);
    padding: 15px 9px 15px 9px;
}
.topic{
    background-color: rgb(246, 246, 246);
    padding: 15px 15px 15px 9px;
    font-weight: 700;
    cursor: pointer;
}
.topic.selected{
    background-color: rgb(236, 236, 236);
}
.qna{
    background-color: white;
    padding: 6px 15px 6px 9px;
    box-shadow: 0 2px 3px rgb(52 58 64 / 6%);
    margin-bottom: 9px;
    border-radius: 3px;
}
.qna .question{
    cursor: pointer;
}
.qna .answer{
    color: rgb(150, 150, 150);
    margin-top: 9px;
    display: none;
}
.selected.qna .answer{
    display: block;
}
#qnaSearch input{
    padding: 6px 15px 6px 9px;
    margin-right: 5px;
}
#qnaSearch button{
    background-color: rgb(246, 246, 246);
    border: none;
    cursor: pointer;
}
#openSupportTicket{
    margin-top: 15px;
    display: flex;
    align-items: center;
    font-weight: 700;
}
#openSupportTicket button{
    background: rgb(0, 158, 231);
    padding: 6px 15px 6px 15px;
    color: white;
    border: none;
    margin-left: 15px;
    cursor: pointer;
}
</style>
