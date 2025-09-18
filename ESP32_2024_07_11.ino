//CONFIGURACIÓN PINES

const int pinesSENSORES[] = {25,26};
const int numSensores = sizeof(pinesSENSORES) / sizeof(pinesSENSORES[0]);

//CONFIGURACIÓN VARIABLES CONTEO

char* variacion = "nada";

bool posibleEntrada = false;
bool posibleSalida = false;

unsigned long tiempo_empiezaDetectar[numSensores] = {0, 0};
unsigned long tiempo_dejaDetectar[numSensores] = {0, 0};

//Máquina de estados

#define NADIE 0
#define PERSONA_DETECTADA 1

int estado[numSensores] = {NADIE, NADIE};
int estado_siguiente[numSensores] = {NADIE, NADIE};

//LED RGB

// #include <Adafruit_NeoPixel.h>

// Adafruit_NeoPixel LED_RGB(1,48, NEO_GRBW + NEO_KHZ800);

// bool LED_cambio_temporal = false;
// unsigned long tiempo_cambio_LED = 0;
// const unsigned long duracion_cambio_LED = 1000;

//CONEXIÓN CON EL SERVER

#include <WiFi.h>

const char* ssid      = "TFG Bruno";
const char* password  = "1012446588";
const char* server_ip = "192.168.1.1";
const int server_port = 12345;

const int id_dispositivo = 2;
int numero_secuencia     = 0;

unsigned long ultima_actualizacion          = 0;
const unsigned long intervalo_actualizacion = 60000;

WiFiClient client;

void setup() {

  Serial.begin(9600);

  for (int i = 0; i < numSensores; i++) {
    pinMode(pinesSENSORES[i], INPUT_PULLUP);
  }
  
//  LED_RGB.begin();
//  LED_RGB.setBrightness(150);
//  LED_RGB.setPixelColor(0, uint32_t(LED_RGB.Color(255,0,0)));   //Rojo
//  LED_RGB.show();

  delay(10);

  conectarWifi();

  conectarServer();

}

void loop() {

  int lectura[numSensores];
  
  for (int i = 0; i < numSensores; i++){
    lectura[i] = digitalRead(pinesSENSORES[i]);

    estado[i] = estado_siguiente[i];

    if (estado[i] == NADIE){
      if (lectura[i] == LOW){
        tiempo_empiezaDetectar[i] = millis();
        estado_siguiente[i] = PERSONA_DETECTADA;
      }
    }
    else if (estado[i] == PERSONA_DETECTADA){
      if (lectura[i] == HIGH){
        tiempo_dejaDetectar[i] = millis();
        estado_siguiente[i] = NADIE;
      }
    }
  }

  if (lectura[0] == LOW && lectura[1] == LOW){
    if (tiempo_empiezaDetectar[1] > tiempo_empiezaDetectar[0] && !posibleSalida){
      posibleEntrada = true;
    }
    else if (tiempo_empiezaDetectar[0] > tiempo_empiezaDetectar[1] && !posibleEntrada){
      posibleSalida = true;

    }
  }
  
  if(lectura[0] == HIGH && lectura[1] == HIGH){
    if (tiempo_dejaDetectar[1] > tiempo_dejaDetectar[0] && posibleEntrada){
      Serial.println("Incrementa");
      variacion = "incrementa";
//      cambiarColorTemporal(uint32_t(LED_RGB.Color(0,255,0)));   //Verde
      enviarDatos();
      ultima_actualizacion = millis();
    }
    else if (tiempo_dejaDetectar[0] > tiempo_dejaDetectar[1] && posibleSalida){
      Serial.println("Decrementa"); 
      variacion = "decrementa";
//      cambiarColorTemporal(uint32_t(LED_RGB.Color(255,255,0)));   //Amarillo
      enviarDatos();
      ultima_actualizacion = millis();
    }
    variacion = "nada";
    posibleEntrada = false;
    posibleSalida = false;
  } 

  if ( millis() - ultima_actualizacion >= intervalo_actualizacion ){
    enviarDatos();
    ultima_actualizacion = millis();
  }

  if (WiFi.status() != WL_CONNECTED){
    conectarWifi();
  }

  if(!client.connected()){
    //LED_RGB.setPixelColor(0, uint32_t(LED_RGB.Color(255,0,0)));   //Rojo
    //LED_RGB.show();
    conectarServer();
  }

//  actualizarLED();

  //delay (50);

}

void conectarWifi(){

  Serial.println();
  Serial.println();
  Serial.print("Conectando a la red WiFi ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.print("Conectado a la red WiFi ");
  Serial.println(ssid);
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());

}

void conectarServer(){

  int intentos = 0;
  Serial.println("Conectando al server...");
  delay (3000);

  while (intentos < 5 && !client.connected()){
    delay(750);
    client.connect(server_ip, server_port);
    intentos++;
    Serial.print("Intento nº: ");
    Serial.println(intentos);
  }

  while (intentos >= 5 && !client.connected()){
    delay(120000);
    client.connect(server_ip, server_port);
    intentos++;
    Serial.print("Intento nº: ");
    Serial.println(intentos);
  }

  Serial.println("Conectado al server ☺");
  //LED_RGB.setPixelColor(0, uint32_t(LED_RGB.Color(0,0,255)));   //Azul
  //LED_RGB.show();

  numero_secuencia++;
  String presentacion = String(id_dispositivo) + "," + String(numero_secuencia) + "," + String("presentacion");

  Serial.print("Enviando presentacion al servidor: ");
  Serial.println(presentacion);

  client.print(presentacion);

}

void enviarDatos(){

  numero_secuencia++;

  String mensaje = String(id_dispositivo) + "," + String(numero_secuencia) + "," + String(variacion);

  Serial.print("Enviando datos al servidor: ");
  Serial.println(mensaje);

  client.print(mensaje);
}

//void cambiarColorTemporal(uint32_t color){
//  LED_RGB.setPixelColor(0, color);
//  LED_RGB.show();
//  LED_cambio_temporal = true;
//  tiempo_cambio_LED = millis();
//}

//void actualizarLED(){
//  if (LED_cambio_temporal && millis() - tiempo_cambio_LED >= duracion_cambio_LED){
//   LED_RGB.setPixelColor(0, uint32_t(LED_RGB.Color(0,0,255)));   // Azul
//    LED_RGB.show();
//  }
//}