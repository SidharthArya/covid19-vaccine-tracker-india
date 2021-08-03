Vue.use(VueTables.ClientTable);

const State = { template: '<div>State: {{ $route.params.state }} </div>' }
const District = { template: '<div>District: </div>' }

const routes = [
  { path: '/state/:state', component: State },
  { path: '/district/:district', component: District },
]
const router = new VueRouter({
  routes 
})

const app = new Vue({
  router
}).$mount('#app')

    data() {
        return {
            states: []
        }
    }
    mounted() {
        fetch("https://cdn-api.co-vin.in/api/v2/admin/location/states",
              headers = {
                  "accept": "application/json",
                  "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36",
              })
            .then(res => res.json())
            .then(data => this.jobs = data),
            .catch(err => console.log(err.message))
        
    }
