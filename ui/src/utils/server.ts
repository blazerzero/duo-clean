import axios from 'axios'

export default axios.create({
    baseURL: 'http://167.71.155.153:5000/duo/api',
    headers: { 'Cache-Control': 'no-cache' },
})