function estimatedCSI = LSestimate(PilotSignal,ReceiveSignal)
estimatedCSI = (PilotSignal' * ReceiveSignal)/(norm(PilotSignal)^2);