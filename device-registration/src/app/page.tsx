'use client';

import { Button, Input, Stack } from "@chakra-ui/react";
import { useState } from "react";
import '@fontsource/ibm-plex-sans'; // Import IBM Plex Sans font

export default function Home() {
  const [macAddress, setMacAddress] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  return (
    <div className="flex flex-col items-center justify-center min-h-screen py-2" style={{ fontFamily: 'IBM Plex Sans, sans-serif' }}>
      <h1 className="text-4xl">
        Device Registration
      </h1>
      <Stack className="sm:p-20">
        <Input placeholder="MAC Address" variant="flushed" onChange={(e) => setMacAddress(e.target.value)}/>
        <Input placeholder="Username" variant="flushed" onChange={(e) => setUsername(e.target.value)}/>
        <Input placeholder="Password" variant="flushed" onChange={(e) => setPassword(e.target.value)}/>
        <Button variant="surface" className="mt-4" width="100%">
          Register
        </Button>
      </Stack>
      
    </div>
  );
}
