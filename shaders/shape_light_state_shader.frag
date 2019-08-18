#define PATH_MODE

#include "shape_shader_common"

#define sLightMap sTD2DInputs[0]
#define sColors sTD2DInputs[1]
#define sAttrs sTD2DInputs[3]
#define sTexParams sTD2DInputs[2]
uniform samplerBuffer sLightCoords;

/*
r: light index (global), aka the sample
   to use when grabbing values from a chop
   with a sample for each light
g: segment index, aka the x coord in the map
b: shape index
a: vertex
*/

void loadLightCoords(inout VertexAttrs attrs, int lightIndex, int shapeIndex) {
    //
}

out vec4 fragColor;
void main() {
    vec4 lightMapVals = texture(sLightMap, vUV.st);
    int lightIndex = int(lightMapVals.r);
    int segIndex = int(lightMapVals.g);
    int shapeIndex = int(lightMapVals.b);
    float vertex = lightMapVals.a;
    VertexAttrs attrs;

    loadLightCoords(attrs, lightIndex, shapeIndex);
    // This must happen after loadLightCoords() because it depends on/modifies the uvs
    loadBasicVertexAttrs(attrs, shapeIndex, sTexParams, sColors, sAttrs);


    vec4 color;
    if (lightIndex < 0) {
        color = vec4(0);
    } else {
        color = texelFetch(sColors, ivec2(shapeIndex, 0), 0);
    }
    fragColor = TDOutputSwizzle(color);
}
