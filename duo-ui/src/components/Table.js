import React, { Component } from 'react';
import BootstrapTable from 'react-bootstrap-table-next';
import { Table, Row, Col } from 'react-bootstrap';

export default class Table extends Component {
    
    constructor(props) {
        super(props);
        this.state = {
            header: this.props.header,
        }
    }

    render() {
        /* const products = [];
        const columns = [{
            dataField: 'id',
            text: 'Product ID'
        }, {
            dataField: 'name',
            text: 'Product Name'
        }, {
            dataField: 'price',
            text: 'Product Price'
        }]; */
        return (
          {/* <BootstrapTable keyField='id' data={ products } columns={ columns } />*/}
          <Table>
            <thead>
              <th>Noisy Tuple?</th>
            </thead>
            <tbody>
              <tr>
                <td>
                  
                </td>
              </tr>
            </tbody>
          </Table>
        )
    }
}
