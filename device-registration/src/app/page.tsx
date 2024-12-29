'use client';

import { Button, Input, Stack } from "@chakra-ui/react";
import { useState } from "react";
import '@fontsource/ibm-plex-sans';
import axios from 'axios';
const API_URL = process.env.NEXT_PUBLIC_API_URL;


async function connectSerial() { // Connect to ESP32 (cu.wchuusbserial)
  const log = document.getElementById('target');
    
  try {
    const port = await navigator.serial.requestPort();
    await port.open({ baudRate: 9600 });
    
    const decoder = new TextDecoderStream(); // Decodes incoming data from ESP32
    
    port.readable.pipeTo(decoder.writable);

    const inputStream = decoder.readable;
    const reader = inputStream.getReader();
    let macAddress = "";
    while (true) {
      const { value, done } = await reader.read();
      if (value) {
        console.log('[readLoop] value:', value, "length:", value.length);
        if (value.length == 19) { // MAC Address are 17 characters long + 2 newlines
          macAddress = value;
          reader.releaseLock();
          break;
        }
      }
      if (done) {
        console.log('[readLoop] DONE', done);
        reader.releaseLock();
        break;
      }
    }
    return macAddress;

  
  } catch (error) {
    console.error('There was an error reading the data:', error);
  }
}

export default function Home() {
  const [macAddress, setMacAddress] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [connected, setConnected] = useState(false);

  function handleRegister() {
    axios.post(`${API_URL}/register`, {
      macAddress,
      username,
      password
    }).then((res) => {
      alert("Device registered successfully");
    }).catch((err) => {
      alert("Failed to register device");
      console.error(err);
    });
  }

  function handleConnect() {
    if (navigator.serial) {
      connectSerial().then(address => {
        if (address) {
          setMacAddress(address);
          setConnected(true);
        }
      });
    } else {
      alert("Web Serial API not supported in this browser, install the latest version of Chrome or Edge");
    }
  }


  return (
    <div className="flex flex-col items-center justify-center min-h-screen py-2" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>
      <h1 className="text-4xl">
        Device Registration
      </h1>
      <Stack className="sm:p-20">
        <Input placeholder="MAC Address" variant="flushed" value={macAddress} readOnly/>
        {!connected && (<Button variant="surface" width="100%" onClick={handleConnect}>
          Connect to device
        </Button>)}
        <Input placeholder="Username" variant="flushed" onChange={(e) => setUsername(e.target.value)}/>
        <Input placeholder="Password" variant="flushed" onChange={(e) => setPassword(e.target.value)}/>
        <Button variant="surface" className="mt-4" width="100%" onClick={handleRegister}>
          Register
        </Button>
      </Stack>
      
    </div>
  );
}
