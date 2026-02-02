import React, { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, Table, Tag, Select, Space, Empty, Typography, Drawer, Descriptions } from 'antd';
import { FileTextOutlined, ThunderboltOutlined, DisconnectOutlined } from '@ant-design/icons';
import { api } from '../api/client';
import type { ColumnsType } from 'antd/es/table';
import { LogEvent } from '../api/types';

const { Option } = Select;
const { Text } = Typography;

const PRIORITY_COLORS: Record<string, string> = {
  'Critical': 'red',
  'Error': 'volcano',
  'Warning': 'orange',
  'Notice': 'gold',
  'Info': 'blue',
  'Debug': 'default'
};

const Logs: React.FC = () => {
  // 1. Fetch Active Containers
  const { data: containers } = useQuery({
    queryKey: ['containers'],
    queryFn: () => api.listContainers(),
  });

  const [selectedContainerId, setSelectedContainerId] = useState<string | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [selectedLog, setSelectedLog] = useState<LogEvent | null>(null);
  
  // WebSocket State
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const MAX_LOGS = 300;

  // Auto-select first container
  useEffect(() => {
    if (containers && containers.length > 0 && !selectedContainerId) {
      setSelectedContainerId(containers[0].id);
    }
  }, [containers, selectedContainerId]);

  // WebSocket Connection
  useEffect(() => {
    if (!selectedContainerId) return;

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    setLogs([]); // Clear logs on switch
    
    // Determine WS URL
    // Better to use relative path if proxy is set up, or configurable base URL
    const baseUrl = api.baseURL || 'http://localhost:8000';
    // Remove /api from baseUrl if it exists, as wsUrl adds /api/logs/ws/...
    // Wait, api.baseURL is like "/infrasecurity/api" or "/api".
    // Our WebSocket endpoint is at /api/logs/ws/{container_id}.
    // If api.baseURL includes /api, we should be careful not to double it.
    // Let's check api/client.ts:
    // const apiPrefix = (import.meta.env.BASE_URL || '/').replace(/\/$/, '');
    // const API_BASE = `${apiPrefix}/api`;
    // So API_BASE is e.g. "/api".
    
    // The WS endpoint is defined in api/app/routers/logs.py as @router.websocket("/ws/{container_id}")
    // And mounted in api/app/main.py as app.include_router(logs.router, prefix="/api/logs", ...)
    // So the full path is /api/logs/ws/{container_id} (relative to API root).
    
    // If we are proxying, we need to respect that.
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    
    // Construct WS URL. 
    // If API_BASE is absolute (http://...), replace protocol.
    // If API_BASE is relative (/api...), append to host.
    
    let wsUrl = '';
    if (baseUrl.startsWith('http')) {
        wsUrl = baseUrl.replace(/^http/, 'ws');
    } else {
        wsUrl = `${wsProtocol}//${window.location.host}${baseUrl}`;
    }
    
    // Now append the endpoint path. 
    // API_BASE already includes /api. 
    // The router is mounted at /logs.
    // So we append /logs/ws/{id}.
    wsUrl = `${wsUrl}/logs/ws/${selectedContainerId}`;

    console.log(`Connecting to WebSocket: ${wsUrl}`);
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket Connected');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const logData = JSON.parse(event.data);
        // Adapt format if necessary. Backend sends raw dict.
        // Frontend expects: timestamp (iso string), priority, rule, source, output, tags
        const newLog: LogEvent = {
          timestamp: new Date(logData.timestamp * 1000).toISOString(),
          rule: logData.rule,
          priority: logData.priority,
          source: logData.source,
          output: logData.output, // output is already JSON string in backend
          tags: JSON.parse(logData.tags || '[]')
        };

        setLogs(prev => {
          const updated = [newLog, ...prev];
          if (updated.length > MAX_LOGS) {
            return updated.slice(0, MAX_LOGS);
          }
          return updated;
        });
      } catch (err) {
        console.error('Error parsing log message:', err);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket Disconnected');
      setIsConnected(false);
    };

    ws.onerror = (err) => {
      console.error('WebSocket Error:', err);
      setIsConnected(false);
    };

    wsRef.current = ws;

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [selectedContainerId]);


  const columns: ColumnsType<LogEvent> = [
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      width: 200,
      render: (ts) => new Date(ts).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' }),
    },
    {
      title: 'Priority',
      dataIndex: 'priority',
      key: 'priority',
      width: 100,
      render: (priority) => (
        <Tag color={PRIORITY_COLORS[priority] || 'default'}>
          {priority ? priority.toUpperCase() : 'UNKNOWN'}
        </Tag>
      ),
    },
    {
      title: 'Rule',
      dataIndex: 'rule',
      key: 'rule',
      width: 150,
      render: (text) => <b>{text}</b>,
    },
    {
      title: 'Output',
      dataIndex: 'output',
      key: 'output',
      render: (text) => (
        <Text code style={{ display: 'block', maxWidth: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {text}
        </Text>
      ),
    },
    {
      title: 'Action',
      key: 'action',
      render: (_, record) => (
        <a onClick={() => {
          setSelectedLog(record);
          setDrawerVisible(true);
        }}>Details</a>
      ),
    },
  ];

  if (!containers || containers.length === 0) {
    return (
      <Card title="Container Logs">
        <Empty description="No active containers found" />
      </Card>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        
        {/* Container Selector */}
        <Card>
          <Space>
            <span>Container:</span>
            <Select
              style={{ width: 300 }}
              value={selectedContainerId}
              onChange={setSelectedContainerId}
              placeholder="Select a container"
            >
              {containers.map(c => (
                <Option key={c.id} value={c.id}>{c.name}</Option>
              ))}
            </Select>
            {isConnected ? (
                <Tag icon={<ThunderboltOutlined />} color="success">Live Streaming</Tag>
            ) : (
                <Tag icon={<DisconnectOutlined />} color="error">Disconnected</Tag>
            )}
          </Space>
        </Card>

        {/* Logs Table */}
        <Card 
          title={
            <Space>
              <FileTextOutlined />
              <span>Security Events Log (Real-time Buffer: {logs.length}/{MAX_LOGS})</span>
            </Space>
          }
        >
          <Table 
            dataSource={logs} 
            columns={columns} 
            rowKey={(record, index) => `${record.timestamp}-${index}`}
            pagination={{ pageSize: 20 }}
            scroll={{ x: 1000 }}
            locale={{ emptyText: isConnected ? 'Waiting for events...' : 'No logs (disconnected)' }}
            onRow={(record) => ({
              onClick: () => {
                setSelectedLog(record);
                setDrawerVisible(true);
              },
              style: { cursor: 'pointer' }
            })}
          />
        </Card>

        <Drawer
          title="Log Details"
          placement="right"
          width={600}
          onClose={() => setDrawerVisible(false)}
          open={drawerVisible}
        >
          {selectedLog && (
            <Descriptions column={1} bordered>
              <Descriptions.Item label="Time">
                {new Date(selectedLog.timestamp).toLocaleString('zh-CN', { timeZone: 'Asia/Shanghai' })}
              </Descriptions.Item>
              <Descriptions.Item label="Priority">
                <Tag color={PRIORITY_COLORS[selectedLog.priority] || 'default'}>
                  {selectedLog.priority ? selectedLog.priority.toUpperCase() : 'UNKNOWN'}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Rule">{selectedLog.rule}</Descriptions.Item>
              <Descriptions.Item label="Source">{selectedLog.source}</Descriptions.Item>
              <Descriptions.Item label="Tags">
                {selectedLog.tags?.map(tag => <Tag key={tag}>{tag}</Tag>)}
              </Descriptions.Item>
              <Descriptions.Item label="Output">
                <Text code>{selectedLog.output}</Text>
              </Descriptions.Item>
            </Descriptions>
          )}
        </Drawer>
      </Space>
    </div>
  );
};

export default Logs;
