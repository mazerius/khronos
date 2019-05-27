# Khronos: a middleware for simplified time management in Cyber Physical Systems.

This project is the software implementation of Khronos, the middleware proposed in [1] and presented at the conference DEBS2019. 
Khronos allows the developers to precisely trade off timeliness versus completeness of the data produced by the underlying CPS infrastructure.
The middleware shields the application developer from the burden of manually specifying timeouts for each data stream, by supporting the specification of completeness constraints: the minimum fraction of packets expected to have arrived from a device data stream.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

1. Start Khronos
```
$ python3 khronos.py, located in /src
```
2. Start GatewayManager, located in /src/cps_communication
```
python3 GatewayManager.py
```
3. Run an example application, located in /src/example_applications
```
python3 client_constraint.py
```

### Prerequisites


```
Python3.6
```


## Deployment

GatewayManager is currently the only component that can be deployed on a different device than the rest of the middleware. 

Make sure to configure gm_config.json, general_config.json correctly by assigning the IP address and port of the device(s) involved in the deployment. 

In these configuration files there are three devices: gateway, gateway_manager and khronos. 

The template assumes that gateway_manager and khronos run on the same device. If not, reconfigure the .json files with the corresponding IP address and port number of each device.

The implementation assumes a gateway that provides a websocket that forwards all incoming sensor data from the CPS network. 


## Authors

**Stefanos Peros** 

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## References

[1]. Waiting for proceedings. 


