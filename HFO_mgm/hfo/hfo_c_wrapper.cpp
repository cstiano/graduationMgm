#include "hfo_c_wrapper.h"


extern "C" {
  hfo::HFOEnvironment* HFO_new() { 
    return new hfo::HFOEnvironment(); 
    }
  void HFO_del(hfo::HFOEnvironment *hfo) { delete hfo; }
  void connectToServer(hfo::HFOEnvironment *hfo,
                       hfo::feature_set_t feature_set,
                       char* config_dir,
                       int server_port,
                       char* server_addr,
                       char* team_name,
                       bool play_goalie,
                       char* record_dir) {
    return hfo->connectToServer(feature_set, config_dir,
                                server_port, server_addr, team_name,
                                play_goalie, record_dir);
  }
  int getStateSize(hfo::HFOEnvironment *hfo) { return hfo->getState().size(); }
  void getState(hfo::HFOEnvironment *hfo, float *state_data) {
    const float* state_features = hfo->getState().data();
    memcpy(state_data, state_features, getStateSize(hfo) * sizeof(float));
  }
  void act(hfo::HFOEnvironment *hfo, hfo::action_t action, float* params) {
    int n_params = NumParams(action);
    std::vector<float> p(n_params);
    for (int i=0; i<n_params; ++i) {
      p[i] = params[i];
    }
    hfo->act(action, p);
  }
  void say(hfo::HFOEnvironment *hfo, const char *message) { hfo->say(message); }
  const char* hear(hfo::HFOEnvironment *hfo) { return hfo->hear().c_str(); }
  hfo::Player playerOnBall(hfo::HFOEnvironment *hfo) { return hfo->playerOnBall(); }
  hfo::status_t step(hfo::HFOEnvironment *hfo) { return hfo->step(); }

  int numParams(const hfo::action_t action) { return NumParams(action); }
  int getUnum(hfo::HFOEnvironment *hfo) {
    return hfo->getUnum();}
  int getNumTeammates(hfo::HFOEnvironment *hfo) {
    return hfo->getNumTeammates();}
  int getNumOpponents(hfo::HFOEnvironment *hfo) {return hfo->getNumOpponents();}
  bool waitAnyState(hfo::HFOEnvironment *hfo) { return hfo->waitAnyState(); }
  bool waitToAct(hfo::HFOEnvironment *hfo) { return hfo->waitToAct(); }
  bool processBeforeBegins(hfo::HFOEnvironment *hfo) { return hfo->processBeforeBegins(); }
  Agent* getAgent(hfo::HFOEnvironment *hfo) {return hfo->getAgent();}
  void setAgent(hfo::HFOEnvironment *hfo, Agent* agent) {hfo->setAgent(agent);}
}