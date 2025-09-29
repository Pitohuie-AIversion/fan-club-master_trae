%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%------------------------------------------------------------------------------%
%                            WESTLAKE UNIVERSITY                              %
%                      ADVANCED SYSTEMS LABORATORY                           %
%------------------------------------------------------------------------------%
%  ███████╗██╗  ██╗ █████╗  ██████╗ ██╗   ██╗ █████╗ ███╗   ██╗ ██████╗       %
%  ╚══███╔╝██║  ██║██╔══██╗██╔═══██╗╚██╗ ██╔╝██╔══██╗████╗  ██║██╔════╝       %
%    ███╔╝ ███████║███████║██║   ██║ ╚████╔╝ ███████║██╔██╗ ██║██║  ███╗      %
%   ███╔╝  ██╔══██║██╔══██║██║   ██║  ╚██╔╝  ██╔══██║██║╚██╗██║██║   ██║      %
%  ███████╗██║  ██║██║  ██║╚██████╔╝   ██║   ██║  ██║██║ ╚████║╚██████╔╝      %
%  ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝       %
%                                                                              %
%  ██████╗  █████╗ ███████╗██╗  ██╗██╗   ██╗ █████╗ ██╗                       %
%  ██╔══██╗██╔══██╗██╔════╝██║  ██║██║   ██║██╔══██╗██║                       %
%  ██║  ██║███████║███████╗███████║██║   ██║███████║██║                       %
%  ██║  ██║██╔══██║╚════██║██╔══██║██║   ██║██╔══██║██║                       %
%  ██████╔╝██║  ██║███████║██║  ██║╚██████╔╝██║  ██║██║                       %
%  ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝                       %
%                                                                              %
%------------------------------------------------------------------------------%
% zhaoyang                   % <mzymuzhaoyang@gmail.com> %                     %
% dashuai                    % <dschen2018@gmail.com>    %                     %
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% FCMkIV External Control MATLAB Broadcast client API demo script %%%%%%%%%
% -------------------------------------------------------------------------
% This example script listens for an external control broadcast and graphs
% the received array data. Notice that the array's dimensions are
% automatically fetched from the broadcast.
% -------------------------------------------------------------------------
% NOTE: The MkIV is expected to be running and with its external control
% broadcast activated.
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
delete(instrfindall);
MAX_VALUE = 16000;
MAX_FANS = 21;
FAWT_FIGURE = 1;
FAWT_NAME = "Basement FAWT";

GRAPH_3D = true;

disp("");
disp("** FCMkIV External Control Broadcast Demo started **");

% Set up broadcast client .................................................
B = FCBroadcastClient();
B.open();

% Build array representation ..............................................
G = '';

% Main loop ...............................................................
disp("Starting main loop");
while true
    b = B.getBroadcast();
    if ~b.isValid()
        disp("Timed out. Terminating");
        break
    elseif isequal(G, '') && GRAPH_3D
        disp("Building FAWT model");
        G = FAWT3DGraph(FAWT_NAME, b.rows, b.columns, MAX_VALUE, 1);
        G.build(FAWT_FIGURE);
    else
        if GRAPH_3D
            G.draw(b.timestamp, b.array);
        else
            disp(b.index);
        end
    end
end
disp("** FCMkIV External Control Broadcast Demo ended **");