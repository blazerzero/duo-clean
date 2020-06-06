import React, { Component } from 'react';
import Table from '../components/Table';
import Header from '../components/Header';

export default class Project extends Component {

    constructor(props) {
        super(props);
    }

    render() {
        return (
            <div className='content-centered site-page'>
                <Header projectId='TBD'/>
                <Table />
            </div>
        )
    }
}