import axios from 'axios'

export default axios.create({
    baseURL: 'http://localhost:5000/duo/api',
    headers: { 'Cache-Control': 'no-cache' },
})